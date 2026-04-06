from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from math import exp, pi
from typing import Any

from app.schemas import (
    BuildDynoSnapshot,
    BuildState,
    DynoCurvePoint,
    DynoResult,
    FactProvenance,
    GearCurve,
    GearCurvePoint,
)
from app.services.build_helpers import active_engine_family, selected_parts, stock_part_ids
from app.services.seed_repository import get_repository
from app.services.simulation_dataset_service import (
    ambient_pressure_kpa,
    get_cooling_calibration_profile,
    get_engine_calibration_profile,
    get_fuel_calibration_profile,
    get_induction_calibration_profile,
    get_reference_dyno_run,
    get_vehicle_resistance_profile,
)

GAS_CONSTANT_AIR = 287.05
GAMMA_AIR = 1.4
PSI_TO_KPA = 6.89476
LBFT_PER_NM = 0.737562
NM_PER_LBFT = 1.0 / LBFT_PER_NM
MPS_TO_MPH = 2.236936


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _source_mode(build: BuildState) -> str:
    repository = get_repository()
    return "licensed" if repository.get_vehicle_record(build.vehicle.trim_id) is not None else "seed"


def _spec_hash(build: BuildState) -> str:
    payload = f"{build.engine_build_spec.model_dump()}|{build.drivetrain_config.model_dump()}"
    return sha256(payload.encode("utf-8")).hexdigest()[:16]


def _displacement_l(build: BuildState) -> float:
    spec = build.engine_build_spec
    cylinder_volume_mm3 = pi * ((spec.bore_mm / 2) ** 2) * spec.stroke_mm
    return (cylinder_volume_mm3 * spec.cylinder_count) / 1_000_000


def _interpolate_curve(curve: tuple[tuple[int, float], ...], rpm: int) -> float:
    if rpm <= curve[0][0]:
        return curve[0][1]
    if rpm >= curve[-1][0]:
        return curve[-1][1]

    for (rpm_a, value_a), (rpm_b, value_b) in zip(curve, curve[1:]):
        if rpm_a <= rpm <= rpm_b:
            span = max(rpm_b - rpm_a, 1)
            ratio = (rpm - rpm_a) / span
            return value_a + ((value_b - value_a) * ratio)
    return curve[-1][1]


def _part_metric(parts: dict[str, object], subsystem: str, field: str) -> float:
    part = parts.get(subsystem)
    if part is None:
        return 0.0
    performance = getattr(part, "performance", None)
    if performance is None:
        return 0.0
    value = getattr(performance, field, 0.0)
    return float(value or 0.0)


def _part_tags(parts: dict[str, object], subsystem: str) -> set[str]:
    part = parts.get(subsystem)
    if part is None:
        return set()
    return {str(tag) for tag in getattr(part, "tags", [])}


def _tire_radius_m(build: BuildState, parts: dict[str, object]) -> float:
    resistance = get_vehicle_resistance_profile(build.vehicle.trim_id)
    tires = parts.get("tires")
    if tires is not None:
        asset_record = get_repository().get_part_record(getattr(tires, "part_id", ""))
        if asset_record is not None:
            radius_from_asset = (
                asset_record.asset_coverage.dimensions.length_mm / 2000
                if asset_record.asset_coverage.dimensions.length_mm
                else 0.0
            )
            if radius_from_asset > 0:
                return radius_from_asset
    return resistance.stock_tire_radius_m


def _gear_speed_mph(rpm: int, gear_ratio: float, final_drive_ratio: float, tire_radius_m: float) -> float:
    wheel_rps = rpm / max(gear_ratio * final_drive_ratio, 0.1) / 60
    speed_mps = wheel_rps * (2 * pi * tire_radius_m)
    return speed_mps * MPS_TO_MPH


def _cam_profile_factor(spec, rpm_ratio: float) -> float:
    top_end = spec.cam_profile.top_end_bias
    low_end = spec.cam_profile.low_end_bias
    intake_bias = spec.cam_profile.intake_bias
    exhaust_bias = spec.cam_profile.exhaust_bias
    if rpm_ratio < 0.42:
        return 1.0 + (low_end * 0.12) + (intake_bias * 0.05) - (top_end * 0.04)
    if rpm_ratio < 0.72:
        return 1.0 + (intake_bias * 0.04) + (exhaust_bias * 0.03)
    return 1.0 + (top_end * 0.12) + (exhaust_bias * 0.05) - (low_end * 0.05)


def _boost_spool_factor(spec, rpm: int, induction_mode: str) -> float:
    if induction_mode == "na":
        return 0.0
    spool_center = 2600 if induction_mode == "turbo" else 2100
    spool_center -= int((spec.exhaust_lift_mm - 10.0) * 40)
    spool_center -= int((spec.lobe_separation_deg - 110.0) * 18)
    spool_width = 520 if induction_mode == "turbo" else 360
    return _clamp(1 / (1 + exp(-(rpm - spool_center) / spool_width)), 0.12, 1.0)


def _fuel_system_multiplier(scale: str) -> float:
    return {
        "stock": 1.0,
        "upgrade": 1.18,
        "high_flow": 1.38,
    }[scale]


def _tune_bias_factor(tune_bias: str) -> tuple[float, float]:
    if tune_bias == "comfort":
        return 0.985, -0.5
    if tune_bias == "aggressive":
        return 1.015, 1.25
    return 1.0, 0.0


def _curve_scale(points: list[DynoCurvePoint], scale: float) -> list[DynoCurvePoint]:
    return [
        DynoCurvePoint(
            rpm=point.rpm,
            torque_lbft=round(point.torque_lbft * scale, 1),
            hp=round((point.torque_lbft * scale) * point.rpm / 5252, 1),
        )
        for point in points
    ]


def _calibrate_curve_shape(
    points: list[DynoCurvePoint],
    *,
    target_peak_hp: float,
    target_peak_torque_lbft: float,
    rev_limit_rpm: int,
) -> tuple[list[DynoCurvePoint], float, float]:
    predicted_peak_hp = max(point.hp for point in points)
    predicted_peak_torque = max(point.torque_lbft for point in points)
    hp_ratio = target_peak_hp / max(predicted_peak_hp, 1.0)
    torque_ratio = target_peak_torque_lbft / max(predicted_peak_torque, 1.0)

    calibrated: list[DynoCurvePoint] = []
    for point in points:
        rpm_ratio = point.rpm / max(rev_limit_rpm, 1000)
        blend = _clamp((rpm_ratio - 0.42) / 0.5, 0.0, 1.0)
        scale = torque_ratio + ((hp_ratio - torque_ratio) * (blend**1.08))
        scaled_torque = point.torque_lbft * scale
        calibrated.append(
            DynoCurvePoint(
                rpm=point.rpm,
                torque_lbft=round(scaled_torque, 1),
                hp=round((scaled_torque * point.rpm) / 5252, 1),
            )
        )

    adjusted_peak_hp = max(point.hp for point in calibrated)
    if adjusted_peak_hp < target_peak_hp:
        fine_scale = target_peak_hp / max(adjusted_peak_hp, 1.0)
        calibrated = [
            DynoCurvePoint(
                rpm=point.rpm,
                torque_lbft=round(point.torque_lbft * fine_scale, 1),
                hp=round(point.hp * fine_scale, 1),
            )
            for point in calibrated
        ]
        hp_ratio *= fine_scale
        torque_ratio *= fine_scale

    return calibrated, torque_ratio, hp_ratio


def _build_matches_reference_baseline(
    build: BuildState,
    *,
    parts: dict[str, object],
) -> bool:
    stock_ids = stock_part_ids(build)
    forced_induction_part = parts.get("forced_induction")
    forced_induction_part_id = getattr(forced_induction_part, "part_id", None)
    forced_induction_tags = _part_tags(parts, "forced_induction")
    stock_forced_induction_id = stock_ids.get("forced_induction")
    if (
        forced_induction_part_id is not None
        and forced_induction_part_id != stock_forced_induction_id
        and "turbo" in forced_induction_tags
        and "turbo" not in build.engine_build_spec.engine_family_id
    ):
        return False
    return True


def build_engine_simulation_snapshot(build: BuildState) -> BuildDynoSnapshot:
    repository = get_repository()
    family = active_engine_family(build, repository=repository)
    parts = selected_parts(build, repository=repository)
    spec = build.engine_build_spec
    drivetrain = build.drivetrain_config

    engine_profile = get_engine_calibration_profile(family.engine_family_id)
    induction_profile = get_induction_calibration_profile(family.engine_family_id)
    fuel_profile = get_fuel_calibration_profile(spec.fuel.fuel_type)
    cooling_profile = get_cooling_calibration_profile(family.cooling_interface.cooling_family)
    resistance_profile = get_vehicle_resistance_profile(build.vehicle.trim_id)
    reference_run = None
    if _build_matches_reference_baseline(build, parts=parts):
        reference_run = get_reference_dyno_run(
            vehicle_id=build.vehicle.trim_id,
            engine_family_id=family.engine_family_id,
            drivetrain_config_id=drivetrain.config_id,
        )

    displacement_l = _displacement_l(build)
    displacement_m3 = displacement_l / 1000
    rod_ratio = spec.rod_length_mm / max(spec.stroke_mm, 1.0)
    ambient_kpa = ambient_pressure_kpa(spec.altitude_m)
    ambient_temp_k = 273.15 + spec.ambient_temp_c
    compressor_efficiency = _clamp(spec.compressor_efficiency, 0.5, 0.88)
    intercooler_effectiveness = _clamp(spec.intercooler_effectiveness, 0.0, 0.95)
    radiator_effectiveness = _clamp(
        spec.radiator_effectiveness + _part_metric(parts, "cooling", "cooling_delta"),
        0.5,
        1.3,
    )
    exhaust_restriction = _clamp(
        spec.exhaust_backpressure_factor
        - (_part_metric(parts, "exhaust", "hp_delta") / 400)
        - (spec.exhaust.flow_bias * 0.12),
        0.72,
        1.35,
    )
    tune_efficiency_factor, tune_timing_bias = _tune_bias_factor(spec.tune_bias)
    ignition_advance_bias = spec.ignition_advance_bias_deg + tune_timing_bias
    tire_radius_m = _tire_radius_m(build, parts)
    forced_induction_part = parts.get("forced_induction")
    forced_induction_tags = _part_tags(parts, "forced_induction")
    tune_tags = _part_tags(parts, "tune")
    fuel_system_tags = _part_tags(parts, "fuel_system")
    induction_mode = spec.induction.type
    effective_boost_target_psi = spec.induction.boost_psi
    if induction_mode == "na" and "turbo" in forced_induction_tags:
        induction_mode = "turbo"
        effective_boost_target_psi = max(
            effective_boost_target_psi,
            9.5
            + (_part_metric(parts, "forced_induction", "hp_delta") / 14)
            + (_part_metric(parts, "tune", "hp_delta") / 65),
        )
        compressor_efficiency = max(compressor_efficiency, 0.74)
        intercooler_effectiveness = max(intercooler_effectiveness, 0.72)
    elif induction_mode != "na":
        effective_boost_target_psi = max(
            effective_boost_target_psi,
            spec.induction.boost_psi + (_part_metric(parts, "tune", "hp_delta") / 90),
        )

    if "turbo" in tune_tags:
        effective_boost_target_psi += 1.1
        ignition_advance_bias -= 0.3
    if "turbo_support" in fuel_system_tags:
        effective_boost_target_psi += 0.4
        spec_target_lambda = min(spec.target_lambda, 0.84)
    else:
        spec_target_lambda = spec.target_lambda
    if _part_metric(parts, "cooling", "cooling_delta") > 0:
        intercooler_effectiveness = max(intercooler_effectiveness, 0.75 + (_part_metric(parts, "cooling", "cooling_delta") * 0.18))
        radiator_effectiveness = min(1.3, radiator_effectiveness + 0.05)

    turbo_overlay_active = induction_mode != "na" and "turbo" in forced_induction_tags and reference_run is None
    effective_rev_limit_rpm = int(
        spec.rev_limit_rpm
        + _part_metric(parts, "engine", "redline_delta_rpm")
        + _part_metric(parts, "tune", "redline_delta_rpm")
    )
    effective_rev_limit_rpm = max(6200, effective_rev_limit_rpm)

    points: list[DynoCurvePoint] = []
    minimum_fuel_limit = 1.0
    minimum_knock_limit = 1.0
    minimum_cooling_limit = 1.0
    minimum_charge_temp_limit = 1.0
    peak_charge_temp_c = spec.ambient_temp_c
    peak_effective_boost_psi = 0.0
    peak_mean_piston_speed = 0.0
    peak_air_mass_flow = 0.0
    peak_fuel_flow = 0.0
    peak_cooling_demand_kw = 0.0
    cooling_capacity_kw = cooling_profile.baseline_rejection_kw * (0.78 + (radiator_effectiveness * 0.35)) * (ambient_kpa / 101.325)

    rpm_points = list(range(2000, effective_rev_limit_rpm + 1, 250))
    for rpm in rpm_points:
        rpm_ratio = rpm / max(effective_rev_limit_rpm, 1000)
        mean_piston_speed = 2 * (spec.stroke_mm / 1000) * rpm / 60
        peak_mean_piston_speed = max(peak_mean_piston_speed, mean_piston_speed)

        ve = _interpolate_curve(engine_profile.ve_curve, rpm)
        ve *= 1 + ((displacement_l - family.base_displacement_l) / max(family.base_displacement_l, 0.1)) * 0.06
        ve *= {"stock": 1.0, "street": 1.035, "race": 1.075}[spec.valve_train.head_flow_stage]
        ve *= _cam_profile_factor(spec, rpm_ratio)
        ve *= 1 + ((spec.intake_cam_duration_deg - engine_profile.default_intake_cam_duration_deg) / 50) * (0.06 if rpm_ratio > 0.6 else -0.03)
        ve *= 1 + ((spec.exhaust_cam_duration_deg - engine_profile.default_exhaust_cam_duration_deg) / 55) * (0.04 if rpm_ratio > 0.55 else -0.02)
        ve *= 1 + ((spec.intake_lift_mm - engine_profile.default_intake_lift_mm) / 6) * (0.05 + (rpm_ratio * 0.03))
        ve *= 1 + ((spec.exhaust_lift_mm - engine_profile.default_exhaust_lift_mm) / 6) * (0.03 + (rpm_ratio * 0.04))
        ve *= 1 - (abs(spec.lobe_separation_deg - engine_profile.default_lobe_separation_deg) / 12) * 0.025
        ve *= 1 + ((rod_ratio - (engine_profile.default_rod_length_mm / max(family.stock_stroke_mm, 1.0))) * (0.03 if rpm_ratio > 0.55 else -0.01))
        ve *= 1 + (_part_metric(parts, "intake", "hp_delta") / 500)
        ve *= 1 + (_part_metric(parts, "forced_induction", "hp_delta") / 700)
        if turbo_overlay_active:
            turbo_top_end_bias = _clamp((rpm_ratio - 0.45) / 0.4, 0.0, 1.0)
            ve *= 0.84 + (0.34 * turbo_top_end_bias)
        ve = _clamp(ve, 0.55, 1.32)

        effective_pressure_ratio = 0.97
        compressor_out_temp_k = ambient_temp_k
        charge_temp_k = ambient_temp_k
        effective_boost_psi = 0.0
        spool_factor = _boost_spool_factor(spec, rpm, induction_mode)
        if induction_mode != "na":
            target_pressure_ratio = (ambient_kpa + (effective_boost_target_psi * PSI_TO_KPA)) / max(ambient_kpa, 1.0)
            effective_pressure_ratio = 1 + ((target_pressure_ratio - 1) * spool_factor * induction_profile.boost_multiplier)
            compressor_out_temp_k = ambient_temp_k * (
                1
                + (
                    ((effective_pressure_ratio ** ((GAMMA_AIR - 1) / GAMMA_AIR)) - 1)
                    / compressor_efficiency
                )
                * induction_profile.charge_heat_multiplier
            )
            cooler_factor = intercooler_effectiveness if induction_mode == "turbo" else intercooler_effectiveness * 0.55
            charge_temp_k = ambient_temp_k + ((compressor_out_temp_k - ambient_temp_k) * (1 - cooler_factor))
            effective_boost_psi = max(0.0, ((ambient_kpa * effective_pressure_ratio) - ambient_kpa) / PSI_TO_KPA)
        else:
            effective_pressure_ratio = _clamp(0.965 - ((exhaust_restriction - 1.0) * 0.06), 0.9, 0.995)

        manifold_pressure_kpa = ambient_kpa * effective_pressure_ratio
        charge_temp_c = charge_temp_k - 273.15
        peak_charge_temp_c = max(peak_charge_temp_c, charge_temp_c)
        peak_effective_boost_psi = max(peak_effective_boost_psi, effective_boost_psi)

        charge_density = (manifold_pressure_kpa * 1000) / (GAS_CONSTANT_AIR * charge_temp_k)
        trapped_air_mass_per_cycle = charge_density * displacement_m3 * ve
        air_mass_flow_kg_s = trapped_air_mass_per_cycle * rpm / 120
        peak_air_mass_flow = max(peak_air_mass_flow, air_mass_flow_kg_s)

        effective_lambda = _clamp(spec_target_lambda, 0.72, 1.02)
        required_fuel_flow_kg_s = air_mass_flow_kg_s / max(fuel_profile.stoich_afr * effective_lambda, 0.1)
        fuel_capacity_kg_s = (
            engine_profile.stock_fuel_flow_capacity_kg_s
            * _fuel_system_multiplier(spec.fuel.injector_scale)
            * _fuel_system_multiplier(spec.fuel.pump_scale)
        )
        fuel_capacity_kg_s *= 1 + (_part_metric(parts, "fuel_system", "driveline_stress_delta") * 4)
        if "turbo_support" in fuel_system_tags:
            fuel_capacity_kg_s *= 1.22
        if "turbo" in tune_tags:
            fuel_capacity_kg_s *= 1.04
        fuel_limit_factor = _clamp(fuel_capacity_kg_s / max(required_fuel_flow_kg_s, 1e-6), 0.72, 1.0)
        minimum_fuel_limit = min(minimum_fuel_limit, fuel_limit_factor)
        fuel_mass_per_cycle = (required_fuel_flow_kg_s * fuel_limit_factor) * 120 / rpm
        peak_fuel_flow = max(peak_fuel_flow, required_fuel_flow_kg_s)

        knock_load = 0.0
        knock_load += max(spec.compression_ratio - (11.3 if induction_mode == "na" else 10.0), 0.0) * 0.11
        knock_load += max(effective_boost_psi - 4.0, 0.0) * 0.038
        knock_load += max(charge_temp_c - 45.0, 0.0) * 0.012
        knock_load += max(ignition_advance_bias, 0.0) * 0.055
        knock_load -= (fuel_profile.knock_resistance - 1.0) * 1.35
        knock_load -= max(intercooler_effectiveness - 0.78, 0.0) * 0.55
        if "turbo" in forced_induction_tags:
            knock_load += 0.08
        knock_limit_factor = _clamp(1.0 - max(knock_load - 0.8, 0.0) * 0.13, 0.78, 1.0)
        minimum_knock_limit = min(minimum_knock_limit, knock_limit_factor)

        lambda_efficiency = 1.0 - (abs(effective_lambda - fuel_profile.best_power_lambda) * 0.58)
        compression_efficiency = 1 + ((spec.compression_ratio - family.compression_ratio) * (0.011 if induction_mode == "na" else 0.007))
        combustion_efficiency = engine_profile.base_combustion_efficiency
        combustion_efficiency *= lambda_efficiency
        combustion_efficiency *= compression_efficiency
        combustion_efficiency *= tune_efficiency_factor
        combustion_efficiency *= 1 + (ignition_advance_bias * 0.008)
        combustion_efficiency = _clamp(combustion_efficiency, 0.24, 0.43)

        work_per_cycle_j = fuel_mass_per_cycle * fuel_profile.lower_heating_value_mj_per_kg * 1_000_000 * combustion_efficiency
        imep_kpa = (work_per_cycle_j / max(displacement_m3, 1e-6)) / 1000
        fmep_kpa = (
            engine_profile.fmep_base_kpa
            + (engine_profile.fmep_speed_coeff * mean_piston_speed)
            + (engine_profile.fmep_speed_sq_coeff * (mean_piston_speed**2))
        )
        pumping_kpa = engine_profile.pumping_base_kpa * exhaust_restriction
        pumping_kpa *= 1.0 if induction_mode == "na" else induction_profile.throttle_pumping_multiplier
        pumping_kpa += max(effective_pressure_ratio - 1.0, 0.0) * 8.5
        pumping_kpa = max(pumping_kpa, 8.0)

        cooling_demand_kw = required_fuel_flow_kg_s * fuel_profile.lower_heating_value_mj_per_kg * 1000 * (1 - combustion_efficiency) * 0.18
        peak_cooling_demand_kw = max(peak_cooling_demand_kw, cooling_demand_kw)
        cooling_limit_factor = 1.0
        cooling_ratio = cooling_capacity_kw / max(cooling_demand_kw, 1.0)
        if cooling_ratio < cooling_profile.thermal_derate_threshold:
            cooling_limit_factor = _clamp(cooling_ratio / cooling_profile.thermal_derate_threshold, 0.82, 1.0)
        minimum_cooling_limit = min(minimum_cooling_limit, cooling_limit_factor)

        charge_temp_limit_factor = 1.0
        if charge_temp_c > cooling_profile.charge_temp_warning_c:
            charge_temp_limit_factor = _clamp(
                1.0 - ((charge_temp_c - cooling_profile.charge_temp_warning_c) * 0.0052),
                0.84,
                1.0,
            )
        minimum_charge_temp_limit = min(minimum_charge_temp_limit, charge_temp_limit_factor)

        bmep_kpa = max(imep_kpa - fmep_kpa - pumping_kpa, 120.0)
        bmep_kpa *= fuel_limit_factor
        bmep_kpa *= knock_limit_factor
        bmep_kpa *= cooling_limit_factor
        bmep_kpa *= charge_temp_limit_factor
        bmep_kpa *= 1 + (_part_metric(parts, "tune", "hp_delta") / 600)
        bmep_kpa *= 1 + (_part_metric(parts, "exhaust", "torque_delta") / 450)
        if turbo_overlay_active:
            turbo_curve_bias = _clamp((rpm_ratio - 0.34) / 0.46, 0.0, 1.0)
            bmep_kpa *= 0.58 + (0.7 * turbo_curve_bias)

        torque_nm = (bmep_kpa * 1000 * displacement_m3) / (4 * pi)
        torque_lbft = max(torque_nm * LBFT_PER_NM, 85.0)
        hp = torque_lbft * rpm / 5252
        points.append(
            DynoCurvePoint(
                rpm=rpm,
                torque_lbft=round(torque_lbft, 1),
                hp=round(hp, 1),
            )
        )

    calibration_scale = 1.0
    torque_calibration_ratio = 1.0
    hp_calibration_ratio = 1.0
    if reference_run is not None and points:
        points, torque_calibration_ratio, hp_calibration_ratio = _calibrate_curve_shape(
            points,
            target_peak_hp=reference_run.peak_hp,
            target_peak_torque_lbft=reference_run.peak_torque_lbft,
            rev_limit_rpm=spec.rev_limit_rpm,
        )
        calibration_scale = (torque_calibration_ratio + hp_calibration_ratio) / 2
        temperature_correction = _clamp(1.0 - (max(spec.ambient_temp_c - 20.0, 0.0) * 0.0015), 0.92, 1.0)
        altitude_correction = _clamp(1.0 - (max(1.0 - (ambient_kpa / 101.325), 0.0) * 0.18), 0.9, 1.0)
        operating_condition_scale = temperature_correction * altitude_correction
        if operating_condition_scale < 0.999:
            points = _curve_scale(points, operating_condition_scale)

    shift_rpm = max(5600, effective_rev_limit_rpm - 150)
    gear_curves: list[GearCurve] = []
    for index, ratio in enumerate(drivetrain.gear_ratios, start=1):
        gear_points: list[GearCurvePoint] = []
        for point in points:
            speed_mph = _gear_speed_mph(point.rpm, ratio, drivetrain.final_drive_ratio, tire_radius_m)
            wheel_torque = point.torque_lbft * ratio * drivetrain.final_drive_ratio * (1 - drivetrain.driveline_loss_factor)
            gear_points.append(
                GearCurvePoint(
                    rpm=point.rpm,
                    speed_mph=round(speed_mph, 1),
                    wheel_torque_lbft=round(wheel_torque, 1),
                )
            )
        gear_curves.append(GearCurve(gear=str(index), points=gear_points))

    dyno = DynoResult(
        peak_hp=round(max(point.hp for point in points), 1),
        peak_torque_lbft=round(max(point.torque_lbft for point in points), 1),
        shift_rpm=shift_rpm,
        engine_curve=points,
        gear_curves=gear_curves,
    )

    limiting_factors: list[dict[str, Any]] = []
    if minimum_knock_limit < 0.995:
        limiting_factors.append(
            {
                "code": "knock_limit",
                "label": "Knock margin",
                "factor": round(minimum_knock_limit, 3),
                "severity": "warning" if minimum_knock_limit > 0.9 else "error",
            }
        )
    if minimum_fuel_limit < 0.995:
        limiting_factors.append(
            {
                "code": "fuel_system_limit",
                "label": "Fuel system headroom",
                "factor": round(minimum_fuel_limit, 3),
                "severity": "warning" if minimum_fuel_limit > 0.9 else "error",
            }
        )
    if minimum_cooling_limit < 0.995:
        limiting_factors.append(
            {
                "code": "cooling_limit",
                "label": "Cooling headroom",
                "factor": round(minimum_cooling_limit, 3),
                "severity": "warning" if minimum_cooling_limit > 0.9 else "error",
            }
        )
    if minimum_charge_temp_limit < 0.995:
        limiting_factors.append(
            {
                "code": "charge_temp_limit",
                "label": "Charge temperature",
                "factor": round(minimum_charge_temp_limit, 3),
                "severity": "warning",
            }
        )

    warnings: list[dict[str, Any]] = []
    if peak_charge_temp_c > cooling_profile.charge_temp_warning_c:
        warnings.append(
            {
                "code": "charge_temp_high",
                "severity": "warning",
                "message": f"Charge temperature peaks around {peak_charge_temp_c:.1f} C, which is above the calibrated comfort threshold.",
                "value": round(peak_charge_temp_c, 1),
            }
        )
    if minimum_cooling_limit < 0.94:
        warnings.append(
            {
                "code": "coolant_headroom_low",
                "severity": "warning",
                "message": "Cooling rejection is approaching the model's derate threshold during a sustained pull.",
                "value": round(minimum_cooling_limit, 3),
            }
        )
    if minimum_fuel_limit < 0.94:
        warnings.append(
            {
                "code": "fuel_system_headroom_low",
                "severity": "warning",
                "message": "Fuel delivery is becoming the limiting factor at the top of the pull.",
                "value": round(minimum_fuel_limit, 3),
            }
        )
    if minimum_knock_limit < 0.94:
        warnings.append(
            {
                "code": "knock_margin_low",
                "severity": "warning",
                "message": "The tune is leaning on knock headroom. Better fuel, cooler charge air, or less timing would widen the margin.",
                "value": round(minimum_knock_limit, 3),
            }
        )

    dominant_limit = limiting_factors[0]["label"] if limiting_factors else "airflow"
    explanation_summary = (
        f"{family.label} simulates at {dyno.peak_hp:.1f} hp and {dyno.peak_torque_lbft:.1f} lb-ft. "
        f"Peak effective boost is {peak_effective_boost_psi:.1f} psi, peak charge temperature is {peak_charge_temp_c:.1f} C, "
        f"and the strongest current limit is {dominant_limit.lower()}."
    )

    confidence = 0.87 if reference_run is not None else 0.76
    basis = (
        "calibrated mean-value engine model using imported engine family, fuel, induction, cooling, and gearing inputs"
        if reference_run is not None
        else "mean-value engine model with imported hardware data but without a direct combo calibration reference"
    )
    assumptions = [
        "This model is a calibrated mean-value engine simulation rather than a 1D wave-action gas-dynamics solver.",
        "Charge temperature, fuel-limit, knock-limit, and cooling derates are resolved across the RPM sweep before gear curves are generated.",
        "Vehicle acceleration modes consume this engine snapshot so dyno, vehicle, and thermal outputs stay in sync.",
    ]
    if reference_run is not None:
        assumptions.append(reference_run.summary)

    return BuildDynoSnapshot(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        engine_family_id=family.engine_family_id,
        spec_hash=_spec_hash(build),
        dyno=dyno,
        computed_at=_now(),
        provenance=FactProvenance(
            source="engine_simulation_service",
            confidence=confidence,
            basis=basis,
            last_verified="2026-04-06",
            kind="simulated",
        ),
        model_version="mean_value_v1",
        derived_values={
            "source_mode": _source_mode(build),
            "reference_calibrated": reference_run is not None,
            "effective_rev_limit_rpm": effective_rev_limit_rpm,
            "displacement_l": round(displacement_l, 3),
            "rod_ratio": round(rod_ratio, 3),
            "ambient_pressure_kpa": round(ambient_kpa, 2),
            "ambient_temp_c": round(spec.ambient_temp_c, 1),
            "altitude_m": round(spec.altitude_m, 1),
            "effective_boost_psi_peak": round(peak_effective_boost_psi, 2),
            "charge_temp_c_peak": round(peak_charge_temp_c, 1),
            "mean_piston_speed_m_s_peak": round(peak_mean_piston_speed, 2),
            "air_mass_flow_kg_s_peak": round(peak_air_mass_flow, 4),
            "fuel_flow_kg_s_peak": round(peak_fuel_flow, 4),
            "cooling_capacity_kw": round(cooling_capacity_kw, 2),
            "cooling_demand_kw_peak": round(peak_cooling_demand_kw, 2),
            "fuel_limit_factor_min": round(minimum_fuel_limit, 3),
            "knock_limit_factor_min": round(minimum_knock_limit, 3),
            "cooling_limit_factor_min": round(minimum_cooling_limit, 3),
            "charge_temp_limit_factor_min": round(minimum_charge_temp_limit, 3),
            "calibration_scale": round(calibration_scale, 4),
            "torque_calibration_ratio": round(torque_calibration_ratio, 4),
            "hp_calibration_ratio": round(hp_calibration_ratio, 4),
            "tire_radius_m": round(tire_radius_m, 4),
            "stock_peak_hp_delta": round(dyno.peak_hp - build.vehicle.stock_hp, 1),
            "stock_peak_torque_delta": round(dyno.peak_torque_lbft - build.vehicle.stock_torque_lbft, 1),
        },
        limiting_factors=limiting_factors,
        warnings=warnings,
        assumptions=assumptions,
        explanation_summary=explanation_summary,
    )
