from __future__ import annotations

import re

from app.schemas import (
    CreateBuildRequest,
    ParsedTargetSpec,
    SimilarityRequest,
    TargetMetrics,
    TargetSpecCandidate,
    TargetSpecRequest,
    TargetSpecResponse,
)
from app.services.build_state_service import create_build
from app.services.metrics_service import build_metric_snapshot
from app.services.scenario_service import build_scenario_snapshot
from app.services.seed_repository import get_repository


_BUDGET_RE = re.compile(r"(?:under|below|budget(?: of)?|around)\s*\$?\s*([0-9][0-9,]{2,})", re.I)
_HP_RE = re.compile(r"([0-9]{3,4})\s*hp", re.I)
_WEIGHT_RE = re.compile(r"(?:under|max|below)\s*([0-9]{4})\s*lb", re.I)
_REDLINE_RE = re.compile(r"([0-9]{4,5})\s*rpm", re.I)


def parse_target_spec(text: str) -> ParsedTargetSpec:
    normalized = text.lower()
    budget_match = _BUDGET_RE.search(text)
    hp_match = _HP_RE.search(text)
    weight_match = _WEIGHT_RE.search(text)
    redline_match = _REDLINE_RE.search(text)

    hard_constraints: dict[str, list[str]] = {}
    if "manual" in normalized:
        hard_constraints["transmission"] = ["manual"]
    if "rwd" in normalized or "rear-wheel" in normalized:
        hard_constraints["drivetrain"] = ["RWD"]
    if "na" in normalized or "naturally aspirated" in normalized:
        hard_constraints["aspiration"] = ["na"]

    use_cases = [label for label in ["daily", "winter", "canyon", "track"] if label in normalized]
    avoid = []
    if "practical" in normalized:
        avoid.append("poor_practicality")
    if "fabrication" in normalized:
        avoid.append("high_fabrication")

    similarity = SimilarityRequest()
    if "gt3 rs" in normalized:
        similarity = SimilarityRequest(
            reference_vehicle="Porsche 911 GT3 RS",
            attributes=["track_bias", "sharp_front_end", "high_revving", "brake_endurance"],
        )

    return ParsedTargetSpec(
        text=text,
        budget_max=float(budget_match.group(1).replace(",", "")) if budget_match else None,
        target_metrics=TargetMetrics(
            budget_max=float(budget_match.group(1).replace(",", "")) if budget_match else None,
            hp_min=float(hp_match.group(1)) if hp_match else None,
            weight_max_lb=float(weight_match.group(1)) if weight_match else None,
            redline_min_rpm=int(redline_match.group(1)) if redline_match else None,
        ),
        hard_constraints=hard_constraints,
        soft_similarity=similarity,
        use_cases=use_cases or ["canyon"],
        avoid=avoid,
        fabrication_tolerance="high" if "fabrication" in normalized else "low",
        legal_tolerance="flexible" if "street legal" not in normalized else "strict",
        confidence=0.78,
    )


def solve_target_spec(request: TargetSpecRequest) -> TargetSpecResponse:
    repository = get_repository()
    parsed = parse_target_spec(request.text)
    candidates: list[TargetSpecCandidate] = []
    scenario_name = parsed.use_cases[0] if parsed.use_cases else "canyon"

    for trim in repository.list_trims():
        baseline = create_build(
            CreateBuildRequest(trim_id=trim.trim_id, scenario_name=scenario_name, target_metrics=parsed.target_metrics)
        )
        for preset in [None, *repository.list_presets()]:
            build = baseline
            if preset is not None and preset.scenario_name != scenario_name and scenario_name != "canyon":
                continue

            patch: dict[str, str] = {}
            if preset is not None:
                patch = preset.patch
                build = baseline.model_copy(
                    update={
                        "selections": [
                            selection.model_copy(
                                update={
                                    "selected_part_id": patch.get(selection.subsystem, selection.selected_part_id),
                                    "source": "preset" if selection.subsystem in patch else selection.source,
                                }
                            )
                            for selection in baseline.selections
                        ]
                    },
                    deep=True,
                )
            metrics = build_metric_snapshot(build).metrics
            scenario = build_scenario_snapshot(build, scenario_name=scenario_name).result

            if parsed.hard_constraints.get("transmission") and trim.transmission not in parsed.hard_constraints["transmission"]:
                continue
            if parsed.hard_constraints.get("drivetrain") and trim.drivetrain not in parsed.hard_constraints["drivetrain"]:
                continue
            if parsed.hard_constraints.get("aspiration") and preset and "turbo" in preset.tags:
                continue
            if parsed.target_metrics.hp_min and metrics.peak_hp < parsed.target_metrics.hp_min:
                continue
            if parsed.target_metrics.weight_max_lb and metrics.curb_weight_lb > parsed.target_metrics.weight_max_lb:
                continue
            if parsed.target_metrics.redline_min_rpm and metrics.redline_rpm < parsed.target_metrics.redline_min_rpm:
                continue
            if parsed.target_metrics.budget_max and metrics.upgrade_cost_usd > parsed.target_metrics.budget_max:
                continue

            score = scenario.score
            why = [f"Scenario score {scenario.score:.1f} in {scenario_name} trim context."]
            if preset:
                why.append(f"Preset overlay: {preset.title}.")
            else:
                why.append("Stock base build kept as baseline candidate.")
            if parsed.soft_similarity.reference_vehicle == "Porsche 911 GT3 RS":
                if metrics.redline_rpm >= 7800:
                    score += 6
                    why.append("Higher rev ceiling moves the build closer to the GT3-style request.")
                if preset and "track" in preset.tags:
                    score += 8
                    why.append("Track-biased preset matches the requested brake endurance and response profile.")
                if metrics.curb_weight_lb < 3100:
                    score += 4
                    why.append("Weight stays relatively light for the target feel.")

            candidates.append(
                TargetSpecCandidate(
                    title=f"{trim.year} {trim.make} {trim.model} {trim.trim}" + (f" with {preset.title}" if preset else ""),
                    trim_id=trim.trim_id,
                    preset_id=preset.preset_id if preset else None,
                    score=round(score, 1),
                    why=why,
                    estimated_metrics=metrics,
                    scenario_name=scenario_name,
                    create_payload=CreateBuildRequest(trim_id=trim.trim_id, scenario_name=scenario_name, target_metrics=parsed.target_metrics),
                    preset_payload=patch,
                )
            )

    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    return TargetSpecResponse(parsed=parsed, candidates=candidates[:5])
