from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import BuildState, DerivedMetricSet, FactProvenance, GearCurve, VehicleMetricSnapshot
from app.services.build_helpers import active_engine_family, selected_parts, stock_part_ids
from app.services.engine_simulation_service import build_engine_simulation_snapshot
from app.services.simulation_dataset_service import get_vehicle_resistance_profile

GRAVITY_MPS2 = 9.80665
LB_TO_KG = 0.45359237
MPS_TO_MPH = 2.236936
M_TO_FT = 3.28084


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _interpolate_wheel_torque(gear_curve: GearCurve, speed_mph: float) -> float:
    points = gear_curve.points
    if not points:
        return 0.0
    if speed_mph <= points[0].speed_mph:
        return points[0].wheel_torque_lbft * 1.05
    if speed_mph >= points[-1].speed_mph:
        return 0.0

    for point_a, point_b in zip(points, points[1:]):
        if point_a.speed_mph <= speed_mph <= point_b.speed_mph:
            span = max(point_b.speed_mph - point_a.speed_mph, 0.1)
            ratio = (speed_mph - point_a.speed_mph) / span
            return point_a.wheel_torque_lbft + ((point_b.wheel_torque_lbft - point_a.wheel_torque_lbft) * ratio)
    return 0.0


def _speed_window(gear_curve: GearCurve) -> tuple[float, float]:
    if not gear_curve.points:
        return (0.0, 0.0)
    return gear_curve.points[0].speed_mph, gear_curve.points[-1].speed_mph


def _force_for_gear(gear_curve: GearCurve, speed_mph: float, tire_radius_m: float) -> float:
    wheel_torque_lbft = _interpolate_wheel_torque(gear_curve, speed_mph)
    return (wheel_torque_lbft * 1.35582) / max(tire_radius_m, 0.1)


def _best_force_at_speed(engine_snapshot, speed_mph: float, tire_radius_m: float) -> tuple[float, int]:
    best_force = 0.0
    best_gear = 1
    for index, gear_curve in enumerate(engine_snapshot.dyno.gear_curves, start=1):
        minimum_speed, maximum_speed = _speed_window(gear_curve)
        if speed_mph > maximum_speed + 0.5:
            continue
        if speed_mph < minimum_speed and index != 1:
            continue
        force = _force_for_gear(gear_curve, speed_mph, tire_radius_m)
        if force > best_force:
            best_force = force
            best_gear = index
    return best_force, best_gear


def _simulate_acceleration(build: BuildState, engine_snapshot, curb_weight_lb: float, tire_radius_m: float) -> tuple[float, float]:
    resistance_profile = get_vehicle_resistance_profile(build.vehicle.trim_id)
    parts = selected_parts(build)
    grip_bonus = sum(part.performance.grip_delta for part in parts.values())
    downforce_bonus = sum(part.performance.downforce_delta for part in parts.values())
    drag_bonus = sum(part.performance.drag_delta for part in parts.values())
    differential_factor = {
        "open": 0.92,
        "street_lsd": 1.0,
        "torsen": 1.02,
        "track_lsd": 1.05,
    }[build.drivetrain_config.differential_bias]

    mass_kg = curb_weight_lb * LB_TO_KG
    rho = 1.225 * (1 - (build.engine_build_spec.altitude_m / 12000))
    cd_area = resistance_profile.cd_area_m2 * (1 + (drag_bonus * 0.12) + (downforce_bonus * 0.04))
    rolling_coeff = max(0.0105, resistance_profile.rolling_resistance_coefficient - (grip_bonus * 0.004))
    launch_mu = resistance_profile.launch_mu * differential_factor * (1 + (grip_bonus * 0.3))
    traction_force_limit = mass_kg * GRAVITY_MPS2 * 0.58 * launch_mu

    dt = 0.05
    speed_mps = 0.0
    elapsed_s = 0.0
    distance_m = 0.0
    zero_to_sixty_s = 0.0
    quarter_mile_s = 0.0
    current_gear = 1
    gear_count = len(engine_snapshot.dyno.gear_curves)

    while elapsed_s < 30.0 and distance_m < 402.3:
        speed_mph = speed_mps * MPS_TO_MPH
        current_curve = engine_snapshot.dyno.gear_curves[current_gear - 1]
        gear_min_speed, gear_max_speed = _speed_window(current_curve)
        if current_gear < gear_count and speed_mph >= max(gear_max_speed - 0.8, gear_min_speed):
            elapsed_s += build.drivetrain_config.shift_latency_ms / 1000
            current_gear += 1
            continue

        wheel_force = _force_for_gear(current_curve, speed_mph, tire_radius_m)
        if current_gear < gear_count:
            next_force = _force_for_gear(engine_snapshot.dyno.gear_curves[current_gear], speed_mph, tire_radius_m)
            if next_force > wheel_force * 1.015:
                elapsed_s += build.drivetrain_config.shift_latency_ms / 1000
                current_gear += 1
                continue

        if speed_mph < 35.0:
            wheel_force = min(wheel_force, traction_force_limit)

        aerodynamic_force = 0.5 * rho * cd_area * (speed_mps**2)
        rolling_force = rolling_coeff * mass_kg * GRAVITY_MPS2
        net_force = max(wheel_force - aerodynamic_force - rolling_force, 0.0)
        acceleration = net_force / max(mass_kg * resistance_profile.drivetrain_inertia_factor, 1.0)
        speed_mps += acceleration * dt
        distance_m += speed_mps * dt
        elapsed_s += dt

        if not zero_to_sixty_s and speed_mph >= 60.0:
            zero_to_sixty_s = elapsed_s
        if distance_m >= 402.3 and not quarter_mile_s:
            quarter_mile_s = elapsed_s

    if not zero_to_sixty_s:
        zero_to_sixty_s = elapsed_s
    if not quarter_mile_s:
        quarter_mile_s = elapsed_s
    return zero_to_sixty_s, quarter_mile_s


def _estimate_top_speed(build: BuildState, engine_snapshot, curb_weight_lb: float, tire_radius_m: float) -> float:
    resistance_profile = get_vehicle_resistance_profile(build.vehicle.trim_id)
    parts = selected_parts(build)
    drag_bonus = sum(part.performance.drag_delta for part in parts.values())
    downforce_bonus = sum(part.performance.downforce_delta for part in parts.values())

    mass_kg = curb_weight_lb * LB_TO_KG
    rho = 1.225 * (1 - (build.engine_build_spec.altitude_m / 12000))
    cd_area = resistance_profile.cd_area_m2 * (1 + (drag_bonus * 0.12) + (downforce_bonus * 0.04))
    rolling_force = resistance_profile.rolling_resistance_coefficient * mass_kg * GRAVITY_MPS2

    top_speed = 0.0
    for speed_mph in [speed / 2 for speed in range(80, 451)]:
        speed_mps = speed_mph / MPS_TO_MPH
        wheel_force, _ = _best_force_at_speed(engine_snapshot, speed_mph, tire_radius_m)
        aero_force = 0.5 * rho * cd_area * (speed_mps**2)
        if wheel_force > aero_force + rolling_force:
            top_speed = speed_mph
        else:
            break
    return max(top_speed, build.vehicle.stock_top_speed_mph - 2.0)


def build_vehicle_metric_snapshot(build: BuildState) -> VehicleMetricSnapshot:
    parts = selected_parts(build)
    stock_ids = stock_part_ids(build)
    engine_family = active_engine_family(build)
    engine_snapshot = build_engine_simulation_snapshot(build)
    dyno = engine_snapshot.dyno
    derived = engine_snapshot.derived_values

    peak_hp = dyno.peak_hp
    peak_torque = dyno.peak_torque_lbft
    curb_weight = build.vehicle.stock_weight_lb + sum(part.performance.weight_delta_lb for part in parts.values())
    curb_weight += engine_family.base_weight_lb - 305

    tire_radius_m = float(derived.get("tire_radius_m", get_vehicle_resistance_profile(build.vehicle.trim_id).stock_tire_radius_m))
    zero_to_sixty, quarter_mile = _simulate_acceleration(build, engine_snapshot, curb_weight, tire_radius_m)
    top_speed = _estimate_top_speed(build, engine_snapshot, curb_weight, tire_radius_m)

    braking_bonus = sum(part.performance.braking_delta for part in parts.values())
    grip_bonus = sum(part.performance.grip_delta for part in parts.values())
    comfort_bonus = sum(part.performance.comfort_delta for part in parts.values())
    downforce_bonus = sum(part.performance.downforce_delta for part in parts.values())
    cooling_bonus = sum(part.performance.cooling_delta for part in parts.values())
    thermal_bonus = sum(part.performance.thermal_delta for part in parts.values())
    driveline_bonus = sum(part.performance.driveline_stress_delta for part in parts.values())

    upgrade_cost = sum(
        parts[subsystem].cost_usd
        for subsystem in parts
        if subsystem in stock_ids and parts[subsystem].part_id != stock_ids[subsystem]
    )
    if build.engine_build_spec.engine_family_id != "fa24d_native":
        upgrade_cost += 9800

    power_to_weight = peak_hp / max(curb_weight / 2000, 0.1)
    braking_distance = max(92.0, build.vehicle.stock_braking_distance_ft - (braking_bonus * 55) - (grip_bonus * 18))
    lateral_grip = min(1.45, build.vehicle.stock_lateral_grip_g + grip_bonus + (downforce_bonus * 0.1))
    thermal_headroom = _clamp(
        build.vehicle.stock_thermal_headroom
        * float(derived.get("cooling_limit_factor_min", 1.0))
        * float(derived.get("charge_temp_limit_factor_min", 1.0))
        + cooling_bonus
        + (thermal_bonus * 0.25),
        0.05,
        1.1,
    )
    driveline_stress = max(
        0.0,
        ((peak_torque - build.vehicle.driveline_limit_lbft) / 180)
        + driveline_bonus
        + (0.08 if build.drivetrain_config.transmission_mode == "automatic" else 0.0),
    )
    comfort_index = _clamp(build.vehicle.stock_comfort_index + comfort_bonus - (grip_bonus * 0.05), 0.2, 1.0)
    fabrication_index = 0.4 if build.engine_build_spec.engine_family_id != "fa24d_native" else 0.0

    metrics = DerivedMetricSet(
        peak_hp=round(peak_hp, 1),
        peak_torque_lbft=round(peak_torque, 1),
        curb_weight_lb=round(curb_weight, 1),
        upgrade_cost_usd=round(upgrade_cost, 0),
        redline_rpm=int(derived.get("effective_rev_limit_rpm", build.engine_build_spec.rev_limit_rpm)),
        power_to_weight_hp_per_ton=round(power_to_weight, 1),
        top_speed_mph=round(top_speed, 1),
        zero_to_sixty_s=round(zero_to_sixty, 2),
        quarter_mile_s=round(quarter_mile, 2),
        braking_distance_ft=round(braking_distance, 1),
        lateral_grip_g=round(lateral_grip, 2),
        thermal_headroom=round(thermal_headroom, 2),
        driveline_stress=round(driveline_stress, 2),
        comfort_index=round(comfort_index, 2),
        fabrication_index=fabrication_index,
        budget_remaining_usd=(
            round(build.target_metrics.budget_max - upgrade_cost, 0)
            if build.target_metrics.budget_max is not None
            else None
        ),
    )
    return VehicleMetricSnapshot(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        metrics=metrics,
        computed_at=_now(),
        provenance=FactProvenance(
            source="vehicle_metrics_service",
            confidence=0.82 if engine_snapshot.derived_values.get("reference_calibrated") else 0.73,
            basis="longitudinal force integration using calibrated engine gear curves, driveline losses, tire radius, aero drag, rolling resistance, and launch traction heuristics",
            last_verified="2026-04-06",
            kind="simulated",
        ),
    )
