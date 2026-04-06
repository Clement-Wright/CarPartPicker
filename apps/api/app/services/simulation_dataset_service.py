from __future__ import annotations

from dataclasses import dataclass
from math import exp

from app.schemas import EngineBuildSpec, EngineFamily


@dataclass(frozen=True)
class EngineCalibrationProfile:
    engine_family_id: str
    default_rod_length_mm: float
    default_intake_cam_duration_deg: float
    default_exhaust_cam_duration_deg: float
    default_intake_lift_mm: float
    default_exhaust_lift_mm: float
    default_lobe_separation_deg: float
    base_combustion_efficiency: float
    stock_fuel_flow_capacity_kg_s: float
    fmep_base_kpa: float
    fmep_speed_coeff: float
    fmep_speed_sq_coeff: float
    pumping_base_kpa: float
    ve_curve: tuple[tuple[int, float], ...]


@dataclass(frozen=True)
class InductionCalibrationProfile:
    engine_family_id: str
    default_compressor_efficiency: float
    default_intercooler_effectiveness: float
    boost_multiplier: float
    charge_heat_multiplier: float
    throttle_pumping_multiplier: float


@dataclass(frozen=True)
class FuelCalibrationProfile:
    fuel_type: str
    stoich_afr: float
    lower_heating_value_mj_per_kg: float
    best_power_lambda: float
    knock_resistance: float


@dataclass(frozen=True)
class CoolingCalibrationProfile:
    cooling_family: str
    baseline_rejection_kw: float
    thermal_derate_threshold: float
    charge_temp_warning_c: float


@dataclass(frozen=True)
class VehicleResistanceProfile:
    vehicle_id: str
    cd_area_m2: float
    rolling_resistance_coefficient: float
    launch_mu: float
    stock_tire_radius_m: float
    drivetrain_inertia_factor: float


@dataclass(frozen=True)
class ReferenceDynoRun:
    vehicle_id: str
    engine_family_id: str
    drivetrain_config_id: str
    peak_hp: float
    peak_torque_lbft: float
    summary: str


ENGINE_CALIBRATION_PROFILES: dict[str, EngineCalibrationProfile] = {
    "fa24d_native": EngineCalibrationProfile(
        engine_family_id="fa24d_native",
        default_rod_length_mm=129.9,
        default_intake_cam_duration_deg=248.0,
        default_exhaust_cam_duration_deg=244.0,
        default_intake_lift_mm=10.6,
        default_exhaust_lift_mm=10.2,
        default_lobe_separation_deg=113.0,
        base_combustion_efficiency=0.345,
        stock_fuel_flow_capacity_kg_s=0.0158,
        fmep_base_kpa=28.0,
        fmep_speed_coeff=4.1,
        fmep_speed_sq_coeff=0.09,
        pumping_base_kpa=18.0,
        ve_curve=(
            (2000, 0.72),
            (2800, 0.82),
            (3600, 0.93),
            (4500, 1.0),
            (5600, 1.02),
            (6600, 0.98),
            (7600, 0.87),
        ),
    ),
    "g16e_turbo_swap": EngineCalibrationProfile(
        engine_family_id="g16e_turbo_swap",
        default_rod_length_mm=128.0,
        default_intake_cam_duration_deg=258.0,
        default_exhaust_cam_duration_deg=254.0,
        default_intake_lift_mm=9.8,
        default_exhaust_lift_mm=9.4,
        default_lobe_separation_deg=110.0,
        base_combustion_efficiency=0.365,
        stock_fuel_flow_capacity_kg_s=0.0165,
        fmep_base_kpa=31.0,
        fmep_speed_coeff=4.3,
        fmep_speed_sq_coeff=0.1,
        pumping_base_kpa=24.0,
        ve_curve=(
            (2200, 0.76),
            (3000, 0.88),
            (3800, 0.98),
            (4700, 1.04),
            (5800, 1.08),
            (6800, 1.04),
            (7800, 0.94),
        ),
    ),
}

INDUCTION_CALIBRATION_PROFILES: dict[str, InductionCalibrationProfile] = {
    "fa24d_native": InductionCalibrationProfile(
        engine_family_id="fa24d_native",
        default_compressor_efficiency=0.72,
        default_intercooler_effectiveness=0.78,
        boost_multiplier=1.0,
        charge_heat_multiplier=1.0,
        throttle_pumping_multiplier=1.0,
    ),
    "g16e_turbo_swap": InductionCalibrationProfile(
        engine_family_id="g16e_turbo_swap",
        default_compressor_efficiency=0.74,
        default_intercooler_effectiveness=0.83,
        boost_multiplier=1.06,
        charge_heat_multiplier=1.08,
        throttle_pumping_multiplier=0.92,
    ),
}

FUEL_CALIBRATION_PROFILES: dict[str, FuelCalibrationProfile] = {
    "91_octane": FuelCalibrationProfile(
        fuel_type="91_octane",
        stoich_afr=14.08,
        lower_heating_value_mj_per_kg=43.0,
        best_power_lambda=0.88,
        knock_resistance=0.97,
    ),
    "93_octane": FuelCalibrationProfile(
        fuel_type="93_octane",
        stoich_afr=14.08,
        lower_heating_value_mj_per_kg=43.2,
        best_power_lambda=0.86,
        knock_resistance=1.0,
    ),
    "e85": FuelCalibrationProfile(
        fuel_type="e85",
        stoich_afr=9.8,
        lower_heating_value_mj_per_kg=29.5,
        best_power_lambda=0.79,
        knock_resistance=1.12,
    ),
}

COOLING_CALIBRATION_PROFILES: dict[str, CoolingCalibrationProfile] = {
    "zn8_stock_cooling": CoolingCalibrationProfile(
        cooling_family="zn8_stock_cooling",
        baseline_rejection_kw=74.0,
        thermal_derate_threshold=0.97,
        charge_temp_warning_c=62.0,
    ),
    "zd8_stock_cooling": CoolingCalibrationProfile(
        cooling_family="zd8_stock_cooling",
        baseline_rejection_kw=73.0,
        thermal_derate_threshold=0.97,
        charge_temp_warning_c=62.0,
    ),
    "swap_frontmount": CoolingCalibrationProfile(
        cooling_family="swap_frontmount",
        baseline_rejection_kw=96.0,
        thermal_derate_threshold=1.04,
        charge_temp_warning_c=66.0,
    ),
    "swap_large_radiator": CoolingCalibrationProfile(
        cooling_family="swap_large_radiator",
        baseline_rejection_kw=92.0,
        thermal_derate_threshold=1.02,
        charge_temp_warning_c=65.0,
    ),
}

VEHICLE_RESISTANCE_PROFILES: dict[str, VehicleResistanceProfile] = {
    "gr86_2022_base": VehicleResistanceProfile(
        vehicle_id="gr86_2022_base",
        cd_area_m2=0.64,
        rolling_resistance_coefficient=0.0144,
        launch_mu=1.02,
        stock_tire_radius_m=0.317,
        drivetrain_inertia_factor=1.035,
    ),
    "gr86_2023_premium": VehicleResistanceProfile(
        vehicle_id="gr86_2023_premium",
        cd_area_m2=0.65,
        rolling_resistance_coefficient=0.0147,
        launch_mu=1.0,
        stock_tire_radius_m=0.323,
        drivetrain_inertia_factor=1.06,
    ),
    "brz_2023_premium": VehicleResistanceProfile(
        vehicle_id="brz_2023_premium",
        cd_area_m2=0.64,
        rolling_resistance_coefficient=0.0144,
        launch_mu=1.01,
        stock_tire_radius_m=0.317,
        drivetrain_inertia_factor=1.035,
    ),
}

REFERENCE_DYNO_RUNS: dict[tuple[str, str, str], ReferenceDynoRun] = {
    ("gr86_2022_base", "fa24d_native", "drivetrain_manual_stock"): ReferenceDynoRun(
        vehicle_id="gr86_2022_base",
        engine_family_id="fa24d_native",
        drivetrain_config_id="drivetrain_manual_stock",
        peak_hp=228.0,
        peak_torque_lbft=184.0,
        summary="Imported stock FA24 manual baseline for the 2022 GR86.",
    ),
    ("gr86_2023_premium", "fa24d_native", "drivetrain_auto_stock"): ReferenceDynoRun(
        vehicle_id="gr86_2023_premium",
        engine_family_id="fa24d_native",
        drivetrain_config_id="drivetrain_auto_stock",
        peak_hp=228.0,
        peak_torque_lbft=184.0,
        summary="Imported stock FA24 automatic baseline for the 2023 GR86 Premium.",
    ),
    ("brz_2023_premium", "fa24d_native", "drivetrain_manual_stock"): ReferenceDynoRun(
        vehicle_id="brz_2023_premium",
        engine_family_id="fa24d_native",
        drivetrain_config_id="drivetrain_manual_stock",
        peak_hp=228.0,
        peak_torque_lbft=184.0,
        summary="Imported stock FA24 manual baseline for the 2023 BRZ Premium.",
    ),
    ("gr86_2022_base", "g16e_turbo_swap", "drivetrain_manual_stock"): ReferenceDynoRun(
        vehicle_id="gr86_2022_base",
        engine_family_id="g16e_turbo_swap",
        drivetrain_config_id="drivetrain_manual_stock",
        peak_hp=300.0,
        peak_torque_lbft=273.0,
        summary="Imported G16 swap manual baseline for the GR86/BRZ swap slice.",
    ),
    ("brz_2023_premium", "g16e_turbo_swap", "drivetrain_manual_stock"): ReferenceDynoRun(
        vehicle_id="brz_2023_premium",
        engine_family_id="g16e_turbo_swap",
        drivetrain_config_id="drivetrain_manual_stock",
        peak_hp=300.0,
        peak_torque_lbft=273.0,
        summary="Imported G16 swap manual baseline for the BRZ swap slice.",
    ),
}

SUPPORTED_CALIBRATED_MODES = {"engine", "vehicle", "thermal"}


def get_engine_calibration_profile(engine_family_id: str) -> EngineCalibrationProfile:
    return ENGINE_CALIBRATION_PROFILES.get(engine_family_id, ENGINE_CALIBRATION_PROFILES["fa24d_native"])


def get_induction_calibration_profile(engine_family_id: str) -> InductionCalibrationProfile:
    return INDUCTION_CALIBRATION_PROFILES.get(engine_family_id, INDUCTION_CALIBRATION_PROFILES["fa24d_native"])


def get_fuel_calibration_profile(fuel_type: str) -> FuelCalibrationProfile:
    return FUEL_CALIBRATION_PROFILES.get(fuel_type, FUEL_CALIBRATION_PROFILES["93_octane"])


def get_cooling_calibration_profile(cooling_family: str | None) -> CoolingCalibrationProfile:
    if cooling_family and cooling_family in COOLING_CALIBRATION_PROFILES:
        return COOLING_CALIBRATION_PROFILES[cooling_family]
    return COOLING_CALIBRATION_PROFILES["zn8_stock_cooling"]


def get_vehicle_resistance_profile(vehicle_id: str) -> VehicleResistanceProfile:
    return VEHICLE_RESISTANCE_PROFILES.get(vehicle_id, VEHICLE_RESISTANCE_PROFILES["gr86_2022_base"])


def get_reference_dyno_run(
    *,
    vehicle_id: str,
    engine_family_id: str,
    drivetrain_config_id: str,
) -> ReferenceDynoRun | None:
    return REFERENCE_DYNO_RUNS.get((vehicle_id, engine_family_id, drivetrain_config_id))


def imported_combo_is_calibrated(
    *,
    vehicle_id: str,
    engine_family_id: str,
    drivetrain_config_id: str,
) -> bool:
    return get_reference_dyno_run(
        vehicle_id=vehicle_id,
        engine_family_id=engine_family_id,
        drivetrain_config_id=drivetrain_config_id,
    ) is not None


def calibration_state_for_mode(
    *,
    source_mode: str,
    vehicle_id: str,
    engine_family_id: str,
    drivetrain_config_id: str,
    mode: str,
) -> str:
    if source_mode == "seed":
        return "seed_heuristic"
    if mode not in SUPPORTED_CALIBRATED_MODES:
        return "calibration_required"
    return (
        "calibrated"
        if imported_combo_is_calibrated(
            vehicle_id=vehicle_id,
            engine_family_id=engine_family_id,
            drivetrain_config_id=drivetrain_config_id,
        )
        else "calibration_required"
    )


def default_engine_spec_updates(
    *,
    engine_family: EngineFamily,
) -> dict[str, float]:
    engine_profile = get_engine_calibration_profile(engine_family.engine_family_id)
    induction_profile = get_induction_calibration_profile(engine_family.engine_family_id)
    fuel_profile = get_fuel_calibration_profile("93_octane")
    return {
        "rod_length_mm": engine_profile.default_rod_length_mm,
        "intake_cam_duration_deg": engine_profile.default_intake_cam_duration_deg,
        "exhaust_cam_duration_deg": engine_profile.default_exhaust_cam_duration_deg,
        "intake_lift_mm": engine_profile.default_intake_lift_mm,
        "exhaust_lift_mm": engine_profile.default_exhaust_lift_mm,
        "lobe_separation_deg": engine_profile.default_lobe_separation_deg,
        "compressor_efficiency": induction_profile.default_compressor_efficiency,
        "intercooler_effectiveness": induction_profile.default_intercooler_effectiveness,
        "target_lambda": fuel_profile.best_power_lambda,
        "ignition_advance_bias_deg": 0.0,
        "exhaust_backpressure_factor": 1.0 if "turbo" not in engine_family.tags else 1.08,
        "radiator_effectiveness": 0.85 if "turbo" not in engine_family.tags else 0.9,
        "ambient_temp_c": 20.0,
        "altitude_m": 0.0,
    }


def hydrate_engine_build_spec(
    spec: EngineBuildSpec,
    *,
    engine_family: EngineFamily,
) -> EngineBuildSpec:
    return spec.model_copy(update=default_engine_spec_updates(engine_family=engine_family))


def ambient_pressure_kpa(altitude_m: float) -> float:
    return 101.325 * exp(-max(altitude_m, 0.0) / 8434.5)
