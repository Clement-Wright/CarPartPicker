from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import BuildState, DerivedMetricSet, FactProvenance, VehicleMetricSnapshot
from app.services.build_helpers import active_engine_family, selected_parts, stock_part_ids
from app.services.engine_simulation_service import build_engine_simulation_snapshot


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_vehicle_metric_snapshot(build: BuildState) -> VehicleMetricSnapshot:
    parts = selected_parts(build)
    stock_ids = stock_part_ids(build)
    engine_family = active_engine_family(build)
    engine_sim = build_engine_simulation_snapshot(build)
    dyno = engine_sim.dyno

    peak_hp = dyno.peak_hp
    peak_torque = dyno.peak_torque_lbft
    curb_weight = build.vehicle.stock_weight_lb + sum(part.performance.weight_delta_lb for part in parts.values())
    curb_weight += engine_family.base_weight_lb - 305
    braking_bonus = sum(part.performance.braking_delta for part in parts.values())
    grip_bonus = sum(part.performance.grip_delta for part in parts.values())
    comfort_bonus = sum(part.performance.comfort_delta for part in parts.values())
    cooling_bonus = sum(part.performance.cooling_delta for part in parts.values())
    thermal_bonus = sum(part.performance.thermal_delta for part in parts.values()) - sum(
        part.geometry.thermal_load for part in parts.values()
    )
    downforce_bonus = sum(part.performance.downforce_delta for part in parts.values())
    drag_bonus = sum(part.performance.drag_delta for part in parts.values())
    driveline_stress = max(0.0, (peak_torque - build.vehicle.driveline_limit_lbft) / 180) + sum(
        part.performance.driveline_stress_delta for part in parts.values()
    )

    upgrade_cost = sum(
        parts[subsystem].cost_usd
        for subsystem in parts
        if subsystem in stock_ids and parts[subsystem].part_id != stock_ids[subsystem]
    )
    if build.engine_build_spec.engine_family_id != "fa24d_native":
        upgrade_cost += 9800
    power_to_weight = peak_hp / (curb_weight / 2000)
    top_speed = build.vehicle.stock_top_speed_mph + ((peak_hp - build.vehicle.stock_hp) * 0.06) - (drag_bonus * 16) + (downforce_bonus * 4)
    zero_to_sixty = max(
        3.1,
        build.vehicle.stock_zero_to_sixty_s
        - ((power_to_weight - (build.vehicle.stock_hp / (build.vehicle.stock_weight_lb / 2000))) * 0.013)
        - (grip_bonus * 0.8),
    )
    quarter_mile = max(10.6, 15.1 - (peak_hp / 82) + (curb_weight / 2250))
    braking_distance = max(92.0, build.vehicle.stock_braking_distance_ft - (braking_bonus * 55) - (grip_bonus * 22))
    lateral_grip = min(1.4, build.vehicle.stock_lateral_grip_g + grip_bonus + (downforce_bonus * 0.12))
    thermal_headroom = max(0.05, build.vehicle.stock_thermal_headroom + cooling_bonus + thermal_bonus - (0.08 if peak_hp > 320 else 0.0))
    comfort_index = max(0.2, min(1.0, build.vehicle.stock_comfort_index + comfort_bonus))
    fabrication_index = 0.4 if build.engine_build_spec.engine_family_id != "fa24d_native" else 0.0

    metrics = DerivedMetricSet(
        peak_hp=round(peak_hp, 1),
        peak_torque_lbft=round(peak_torque, 1),
        curb_weight_lb=round(curb_weight, 1),
        upgrade_cost_usd=round(upgrade_cost, 0),
        redline_rpm=int(build.engine_build_spec.rev_limit_rpm),
        power_to_weight_hp_per_ton=round(power_to_weight, 1),
        top_speed_mph=round(top_speed, 1),
        zero_to_sixty_s=round(zero_to_sixty, 2),
        quarter_mile_s=round(quarter_mile, 2),
        braking_distance_ft=round(braking_distance, 1),
        lateral_grip_g=round(lateral_grip, 2),
        thermal_headroom=round(thermal_headroom, 2),
        driveline_stress=round(max(0.0, driveline_stress), 2),
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
            confidence=0.73,
            basis="vehicle metrics derived from engine simulation, selected subsystem deltas, and deterministic gearing/drag/grip heuristics",
            last_verified="2026-04-04",
            kind="simulated",
        ),
    )
