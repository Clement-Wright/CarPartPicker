from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import BuildScenarioSnapshot, BuildState, FactProvenance, ScenarioResult
from app.services.build_helpers import active_engine_family, selected_parts
from app.services.metrics_service import build_metric_snapshot
from app.services.seed_repository import get_repository
from app.services.validation_service import build_validation_snapshot


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_scenario_snapshot(build: BuildState, scenario_name: str | None = None) -> BuildScenarioSnapshot:
    repository = get_repository()
    scenario_name = scenario_name or build.active_scenario
    scenario = repository.get_scenario(scenario_name)
    metrics = build_metric_snapshot(build).metrics
    validation = build_validation_snapshot(build, phase="fast")
    parts = selected_parts(build)
    engine_family = active_engine_family(build)

    score = 65.0
    strengths: list[str] = []
    penalties: list[str] = []
    notes: list[str] = scenario.assumptions[:]

    score += metrics.lateral_grip_g * scenario.weights.get("grip", 0) * 20
    score += (1 / max(metrics.zero_to_sixty_s, 1)) * scenario.weights.get("power", 0) * 120
    score += (1 / max(metrics.braking_distance_ft, 1)) * scenario.weights.get("braking", 0) * 1800
    score += metrics.comfort_index * scenario.weights.get("comfort", 0) * 20
    score += metrics.thermal_headroom * scenario.weights.get("thermal", 0) * 25
    score += metrics.driveline_stress * scenario.weights.get("stress", 0) * 30
    score += metrics.upgrade_cost_usd / 1000 * scenario.weights.get("cost", 0) * 5

    if validation.summary.blockers:
        score -= validation.summary.blockers * 15
        penalties.append("Hard compatibility blockers remain unresolved.")
    if validation.summary.fabrication_required:
        score -= validation.summary.fabrication_required * 10
        penalties.append("The current configuration needs fabrication tolerance.")

    if scenario_name == "winter":
        if "winter" in parts["tires"].tags:
            strengths.append("Winter tire compound supports cold-weather traction.")
            score += 10
        else:
            penalties.append("Non-winter tire compound reduces cold-weather confidence.")
            score -= 16
        if parts["suspension"].geometry.ride_height_drop_mm > 20:
            penalties.append("Aggressive ride-height drop hurts snow clearance.")
            score -= 12
        if build.engine_build_spec.engine_family_id != "fa24d_native":
            penalties.append("Swap configuration adds cold-weather complexity and service burden.")
            score -= 8

    if scenario_name == "track":
        if metrics.thermal_headroom >= 0.7:
            strengths.append("Cooling headroom supports sustained sessions.")
            score += 10
        else:
            penalties.append("Thermal headroom is thin for repeated hot laps.")
            score -= 12
        if "track" in parts["brakes"].tags:
            strengths.append("Brake package supports repeated high-energy stops.")
            score += 8
        if engine_family.engine_family_id != "fa24d_native":
            strengths.append("Swap engine broadens the performance ceiling for track use.")
            score += 5

    if scenario_name == "daily":
        if metrics.comfort_index >= 0.7:
            strengths.append("Ride and NVH remain reasonable for commute duty.")
        else:
            penalties.append("Comfort tradeoff is noticeable in daily use.")
            score -= 8

    if scenario_name == "canyon" and "canyon" in parts["tires"].tags:
        strengths.append("Tire package suits fast mountain-road pacing.")
        score += 7

    result = ScenarioResult(
        scenario_name=scenario_name,
        score=round(max(0.0, min(score, 99.0)), 1),
        passing=validation.summary.blockers == 0,
        strengths=strengths,
        penalties=penalties,
        notes=notes,
    )
    return BuildScenarioSnapshot(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        result=result,
        computed_at=_now(),
        provenance=FactProvenance(
            source="scenario_service",
            confidence=0.69,
            basis="phase-1 weighted scenario scoring model",
            last_verified="2026-04-04",
            kind="simulated",
        ),
    )
