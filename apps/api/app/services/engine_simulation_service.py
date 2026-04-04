from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from math import pi

from app.schemas import BuildDynoSnapshot, BuildState, DynoCurvePoint, DynoResult, FactProvenance, GearCurve, GearCurvePoint
from app.services.build_helpers import active_engine_family, selected_parts


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _spec_hash(build: BuildState) -> str:
    payload = f"{build.engine_build_spec.model_dump()}|{build.drivetrain_config.model_dump()}"
    return sha256(payload.encode("utf-8")).hexdigest()[:16]


def _displacement_l(build: BuildState) -> float:
    spec = build.engine_build_spec
    cylinder_volume_mm3 = pi * ((spec.bore_mm / 2) ** 2) * spec.stroke_mm
    return (cylinder_volume_mm3 * spec.cylinder_count) / 1_000_000


def build_engine_simulation_snapshot(build: BuildState) -> BuildDynoSnapshot:
    family = active_engine_family(build)
    parts = selected_parts(build)
    spec = build.engine_build_spec
    drivetrain = build.drivetrain_config

    displacement_factor = _displacement_l(build) / max(family.base_displacement_l, 0.1)
    compression_factor = 1 + ((spec.compression_ratio - family.compression_ratio) * 0.018)
    head_factor = {"stock": 1.0, "street": 1.06, "race": 1.11}[spec.valve_train.head_flow_stage]
    cam_factor = 1 + spec.cam_profile.top_end_bias + (spec.cam_profile.low_end_bias * 0.35)
    vvt_factor = 1.02 if spec.valve_train.variable_valve_timing else 0.98
    induction_factor = 1.0
    if spec.induction.type == "turbo":
        induction_factor += (spec.induction.boost_psi / 14.7) * 0.62
    elif spec.induction.type == "supercharger":
        induction_factor += (spec.induction.boost_psi / 14.7) * 0.54
    fuel_factor = {"91_octane": 0.98, "93_octane": 1.0, "e85": 1.06}[spec.fuel.fuel_type]
    injector_factor = {"stock": 1.0, "upgrade": 1.03, "high_flow": 1.05}[spec.fuel.injector_scale]
    pump_factor = {"stock": 1.0, "upgrade": 1.02, "high_flow": 1.04}[spec.fuel.pump_scale]
    tune_factor = {"comfort": 0.98, "balanced": 1.0, "aggressive": 1.05}[spec.tune_bias]
    intake_factor = 1 + (parts["intake"].performance.hp_delta / 220 if "intake" in parts else 0.0)
    exhaust_factor = 1 + (parts["exhaust"].performance.hp_delta / 220 if "exhaust" in parts else 0.0)
    external_boost_factor = 1 + (0.08 if parts.get("forced_induction") and "turbo" in parts["forced_induction"].tags else 0.0)

    peak_hp = family.base_peak_hp * displacement_factor * compression_factor * head_factor * cam_factor * vvt_factor
    peak_hp *= induction_factor * fuel_factor * injector_factor * pump_factor * tune_factor * intake_factor * exhaust_factor * external_boost_factor
    peak_torque = family.base_peak_torque_lbft * displacement_factor * compression_factor
    peak_torque *= induction_factor * fuel_factor * injector_factor * pump_factor * intake_factor * exhaust_factor

    if spec.induction.type == "turbo":
        peak_torque *= 1.08
    if "forced_induction" in parts and "turbo" in parts["forced_induction"].tags:
        peak_torque *= 1.05

    supporting_power_delta = sum(
        parts[subsystem].performance.hp_delta
        for subsystem in ["forced_induction", "intake", "exhaust", "tune"]
        if subsystem in parts
    )
    supporting_torque_delta = sum(
        parts[subsystem].performance.torque_delta
        for subsystem in ["forced_induction", "intake", "exhaust", "tune"]
        if subsystem in parts
    )
    peak_hp += supporting_power_delta
    peak_torque += supporting_torque_delta

    redline_bonus = 0
    if "tune" in parts:
        redline_bonus += parts["tune"].performance.redline_delta_rpm
    if "intake" in parts:
        redline_bonus += int(parts["intake"].performance.redline_delta_rpm)
    redline = max(6200, spec.rev_limit_rpm + redline_bonus)
    shift_rpm = max(5500, redline - 200)

    points: list[DynoCurvePoint] = []
    start_rpm = 2000
    for rpm in range(start_rpm, redline + 1, 400):
        band = rpm / redline
        torque_shape = 0.75 + (spec.cam_profile.low_end_bias * 0.2)
        if band < 0.45:
            torque_multiplier = torque_shape + (band * (0.55 + spec.cam_profile.low_end_bias * 0.35))
        elif band < 0.75:
            torque_multiplier = 1.0 + (spec.cam_profile.top_end_bias * 0.15) - ((band - 0.45) * 0.15)
        else:
            torque_multiplier = 0.94 + (spec.cam_profile.top_end_bias * 0.06) - ((band - 0.75) * (0.46 - spec.cam_profile.top_end_bias * 0.15))
        torque = max(105.0, peak_torque * torque_multiplier)
        hp = torque * rpm / 5252
        points.append(DynoCurvePoint(rpm=rpm, torque_lbft=round(torque, 1), hp=round(hp, 1)))

    max_curve_hp = max(point.hp for point in points)
    max_curve_torque = max(point.torque_lbft for point in points)
    scale_factor = max(peak_hp / max(max_curve_hp, 1), peak_torque / max(max_curve_torque, 1))
    if scale_factor > 1:
        points = [
            DynoCurvePoint(
                rpm=point.rpm,
                torque_lbft=round(point.torque_lbft * scale_factor, 1),
                hp=round((point.torque_lbft * scale_factor) * point.rpm / 5252, 1),
            )
            for point in points
        ]

    tire_diameter_in = 25.0 if build.vehicle.stock_wheel_diameter == 17 else 25.1
    gear_curves: list[GearCurve] = []
    for index, ratio in enumerate(drivetrain.gear_ratios, start=1):
        gear_points: list[GearCurvePoint] = []
        for point in points:
            speed = (point.rpm * tire_diameter_in) / (ratio * drivetrain.final_drive_ratio * 336)
            wheel_torque = point.torque_lbft * ratio * drivetrain.final_drive_ratio * (1 - drivetrain.driveline_loss_factor)
            gear_points.append(
                GearCurvePoint(
                    rpm=point.rpm,
                    speed_mph=round(speed, 1),
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
    return BuildDynoSnapshot(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        engine_family_id=family.engine_family_id,
        spec_hash=_spec_hash(build),
        dyno=dyno,
        computed_at=_now(),
        provenance=FactProvenance(
            source="engine_simulation_service",
            confidence=0.74,
            basis="parameter-based dyno-lite model using engine family, bore/stroke, compression, cam, induction, fuel, tune, and gearing",
            last_verified="2026-04-04",
            kind="simulated",
        ),
    )
