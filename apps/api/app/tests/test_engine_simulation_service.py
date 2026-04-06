from app.schemas import CreateBuildRequest, PatchBuildPartsRequest, PatchDrivetrainRequest, PatchEngineRequest
from app.services.build_state_service import apply_preset, create_build, patch_build, patch_drivetrain, patch_engine
from app.services.engine_simulation_service import build_engine_simulation_snapshot
from app.services.vehicle_metrics_service import build_vehicle_metric_snapshot


def test_stock_manual_and_auto_use_calibrated_baselines_with_different_vehicle_performance() -> None:
    manual_build = create_build(CreateBuildRequest(trim_id="gr86_2022_base", scenario_name="track"))
    auto_build = create_build(CreateBuildRequest(trim_id="gr86_2023_premium", scenario_name="track"))

    manual_engine = build_engine_simulation_snapshot(manual_build)
    auto_engine = build_engine_simulation_snapshot(auto_build)
    manual_vehicle = build_vehicle_metric_snapshot(manual_build)
    auto_vehicle = build_vehicle_metric_snapshot(auto_build)

    assert manual_engine.derived_values["reference_calibrated"] is True
    assert auto_engine.derived_values["reference_calibrated"] is True
    assert manual_engine.dyno.peak_hp >= 228.0
    assert auto_engine.dyno.peak_hp >= 228.0
    assert manual_vehicle.metrics.zero_to_sixty_s < auto_vehicle.metrics.zero_to_sixty_s
    assert manual_build.drivetrain_config.driveline_loss_factor < auto_build.drivetrain_config.driveline_loss_factor


def test_turbo_overlay_uses_uncalibrated_overlay_model_without_falling_back_to_stock_curve() -> None:
    build = create_build(CreateBuildRequest(trim_id="gr86_2022_base", scenario_name="track"))
    build = apply_preset(build.build_id, "preset_turbo_track").build

    snapshot = build_engine_simulation_snapshot(build)

    assert snapshot.derived_values["reference_calibrated"] is False
    assert snapshot.derived_values["effective_boost_psi_peak"] > 15.0
    assert snapshot.dyno.peak_hp >= 430.0
    assert snapshot.dyno.peak_torque_lbft < 420.0
    assert snapshot.dyno.peak_torque_lbft >= 400.0
    assert snapshot.explanation_summary


def test_hot_high_altitude_engine_config_loses_power_and_raises_charge_temp() -> None:
    baseline = create_build(CreateBuildRequest(trim_id="gr86_2022_base", scenario_name="track"))
    stressed = create_build(CreateBuildRequest(trim_id="gr86_2022_base", scenario_name="track"))
    stressed = patch_engine(
        stressed.build_id,
        PatchEngineRequest(
            engine_family_id="g16e_turbo_swap",
            boost_psi=19.0,
            ambient_temp_c=38.0,
            altitude_m=1800.0,
            intercooler_effectiveness=0.62,
        ),
    )

    baseline = patch_engine(
        baseline.build_id,
        PatchEngineRequest(
            engine_family_id="g16e_turbo_swap",
            boost_psi=19.0,
            ambient_temp_c=20.0,
            altitude_m=0.0,
            intercooler_effectiveness=0.82,
        ),
    )

    baseline_snapshot = build_engine_simulation_snapshot(baseline)
    stressed_snapshot = build_engine_simulation_snapshot(stressed)

    assert baseline_snapshot.dyno.peak_hp > stressed_snapshot.dyno.peak_hp
    assert stressed_snapshot.derived_values["charge_temp_c_peak"] > baseline_snapshot.derived_values["charge_temp_c_peak"]
    assert stressed_snapshot.derived_values["charge_temp_limit_factor_min"] <= baseline_snapshot.derived_values["charge_temp_limit_factor_min"]
    assert stressed_snapshot.warnings


def test_final_drive_changes_vehicle_acceleration_and_gear_curve_speed() -> None:
    base_build = create_build(CreateBuildRequest(trim_id="gr86_2022_base", scenario_name="track"))
    short_drive_build = create_build(CreateBuildRequest(trim_id="gr86_2022_base", scenario_name="track"))
    short_drive_build = patch_drivetrain(
        short_drive_build.build_id,
        PatchDrivetrainRequest(final_drive_ratio=4.56),
    )

    base_engine = build_engine_simulation_snapshot(base_build)
    short_engine = build_engine_simulation_snapshot(short_drive_build)
    base_vehicle = build_vehicle_metric_snapshot(base_build)
    short_vehicle = build_vehicle_metric_snapshot(short_drive_build)

    base_first_gear = base_engine.dyno.gear_curves[0].points[-1]
    short_first_gear = short_engine.dyno.gear_curves[0].points[-1]

    assert short_first_gear.speed_mph < base_first_gear.speed_mph
    assert short_vehicle.metrics.zero_to_sixty_s <= base_vehicle.metrics.zero_to_sixty_s
    assert short_vehicle.metrics.top_speed_mph <= base_vehicle.metrics.top_speed_mph


def test_intercooler_and_cooling_support_reduce_temperature_penalties() -> None:
    unsupported = create_build(CreateBuildRequest(trim_id="gr86_2022_base", scenario_name="track"))
    supported = create_build(CreateBuildRequest(trim_id="gr86_2022_base", scenario_name="track"))

    unsupported = patch_engine(
        unsupported.build_id,
        PatchEngineRequest(
            engine_family_id="g16e_turbo_swap",
            boost_psi=20.0,
            ambient_temp_c=34.0,
            intercooler_effectiveness=0.58,
            radiator_effectiveness=0.78,
        ),
    )
    supported = patch_engine(
        supported.build_id,
        PatchEngineRequest(
            engine_family_id="g16e_turbo_swap",
            boost_psi=20.0,
            ambient_temp_c=34.0,
            intercooler_effectiveness=0.84,
            radiator_effectiveness=0.96,
        ),
    )
    supported = patch_build(
        supported.build_id,
        PatchBuildPartsRequest(parts={"cooling": "cooling_track_pack"}),
    )

    unsupported_snapshot = build_engine_simulation_snapshot(unsupported)
    supported_snapshot = build_engine_simulation_snapshot(supported)

    assert supported_snapshot.derived_values["charge_temp_c_peak"] < unsupported_snapshot.derived_values["charge_temp_c_peak"]
    assert supported_snapshot.derived_values["cooling_limit_factor_min"] >= unsupported_snapshot.derived_values["cooling_limit_factor_min"]
