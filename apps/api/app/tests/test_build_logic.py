from app.schemas import CreateBuildRequest, PatchBuildPartsRequest
from app.services.build_state_service import apply_preset, create_build, patch_build
from app.services.metrics_service import build_metric_snapshot
from app.services.scenario_service import build_scenario_snapshot
from app.services.validation_service import build_validation_snapshot


def test_stock_17_wheels_fail_big_brake_clearance() -> None:
    build = create_build(CreateBuildRequest(trim_id="gr86_2022_base", scenario_name="daily"))
    build = patch_build(
        build.build_id,
        PatchBuildPartsRequest(parts={"brakes": "brakes_big_18"}),
    )

    validation = build_validation_snapshot(build)

    assert any("18-inch" in finding.detail for finding in validation.findings)
    assert validation.summary.blockers >= 1


def test_turbo_build_requires_supporting_mods_until_preset_applied() -> None:
    build = create_build(CreateBuildRequest(trim_id="brz_2023_premium", scenario_name="track"))
    build = patch_build(
        build.build_id,
        PatchBuildPartsRequest(parts={"forced_induction": "fi_turbo_street"}),
    )
    validation = build_validation_snapshot(build)
    assert validation.summary.blockers >= 1

    applied = apply_preset(build.build_id, "preset_turbo_track")
    resolved = build_validation_snapshot(applied.build)
    assert resolved.summary.blockers == 0


def test_low_track_ride_height_is_penalized_in_winter() -> None:
    build = create_build(CreateBuildRequest(trim_id="brz_2023_premium", scenario_name="winter"))
    build = patch_build(
        build.build_id,
        PatchBuildPartsRequest(parts={"suspension": "suspension_track", "wheels": "wheels_track_18", "tires": "tires_track_18"}),
    )
    winter_result = build_scenario_snapshot(build, "winter").result
    track_result = build_scenario_snapshot(build, "track").result

    assert winter_result.score < track_result.score
    assert winter_result.penalties


def test_metrics_increase_after_turbo_overlay() -> None:
    build = create_build(CreateBuildRequest(trim_id="gr86_2022_base", scenario_name="track"))
    applied = apply_preset(build.build_id, "preset_turbo_track")
    metrics = build_metric_snapshot(applied.build).metrics

    assert metrics.peak_hp >= 400
    assert metrics.upgrade_cost_usd > 0
