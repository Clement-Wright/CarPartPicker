from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException

from app.schemas import (
    BuildRecommendation,
    BuildRecommendationRequest,
    CurrentSetup,
    PackageSeed,
    PartSeed,
    ScoreBreakdown,
    VehicleTrim,
)
from app.services.explanation_service import recommendation_explanation
from app.services.graph_codec import encode_graph_payload
from app.services.seed_repository import SeedRepository, get_repository


@dataclass
class Evaluation:
    package: PackageSeed
    trim: VehicleTrim
    valid: bool
    reasons: list[str]
    matched_goals: list[str]
    required_changes: list[str]
    conflicts: list[str]
    score_breakdown: ScoreBreakdown | None
    final_score: float
    fitment_confidence: float
    effective_wheel_diameter: int
    parts: list[PartSeed]


def _normalize(value: float) -> float:
    return max(0.0, min(1.0, round(value, 3)))


def derive_current_setup(trim: VehicleTrim, current_setup: CurrentSetup | None) -> CurrentSetup:
    setup = current_setup.model_copy(deep=True) if current_setup else CurrentSetup()
    if setup.wheel_diameter is None:
        setup.wheel_diameter = trim.stock_wheel_diameter
    return setup


def _goal_score(package: PackageSeed, goals: list[str]) -> float:
    if not goals:
        return 0.68
    scores = [package.goal_biases.get(goal, 0.45) for goal in goals]
    return _normalize(sum(scores) / len(scores))


def _cost_efficiency(package: PackageSeed, budget_max: int | None) -> float:
    average_cost = (package.price_band.min + package.price_band.max) / 2
    if budget_max:
        ratio = average_cost / budget_max
        if ratio <= 0.6:
            return 0.96
        if ratio <= 0.8:
            return 0.84
        if ratio <= 1:
            return 0.72
        return 0.0
    if average_cost <= 900:
        return 0.9
    if average_cost <= 1800:
        return 0.78
    if average_cost <= 2600:
        return 0.64
    return 0.44


def _dependency_simplicity(package: PackageSeed) -> float:
    return _normalize(1 - (package.dependency_count * 0.12))


def _fitment_confidence(
    package: PackageSeed, required_changes: list[str], conflicts: list[str]
) -> float:
    return _normalize(package.fitment_base - (0.04 * len(required_changes)) - (0.08 * len(conflicts)))


def _safety_preservation(trim: VehicleTrim, package: PackageSeed, parts: list[PartSeed]) -> float:
    part_safety_delta = sum(part.safety_delta for part in parts)
    return _normalize(
        (trim.safety_index * 0.55) + (package.safety_preservation * 0.45) + part_safety_delta
    )


def evaluate_package(
    *,
    trim: VehicleTrim,
    package: PackageSeed,
    selected_goals: list[str],
    budget_max: int | None,
    current_setup: CurrentSetup | None,
    repository: SeedRepository,
) -> Evaluation:
    if trim.platform not in package.compatible_platforms:
        return Evaluation(
            package=package,
            trim=trim,
            valid=False,
            reasons=["Package does not fit this platform."],
            matched_goals=[],
            required_changes=[],
            conflicts=[],
            score_breakdown=None,
            final_score=0.0,
            fitment_confidence=0.0,
            effective_wheel_diameter=trim.stock_wheel_diameter,
            parts=[],
        )

    if package.compatible_trim_ids and trim.trim_id not in package.compatible_trim_ids:
        return Evaluation(
            package=package,
            trim=trim,
            valid=False,
            reasons=["Package is not approved for this trim."],
            matched_goals=[],
            required_changes=[],
            conflicts=[],
            score_breakdown=None,
            final_score=0.0,
            fitment_confidence=0.0,
            effective_wheel_diameter=trim.stock_wheel_diameter,
            parts=[],
        )

    parts = repository.expand_parts(package)
    setup = derive_current_setup(trim, current_setup)
    wheel_part = next((part for part in parts if part.category == "wheel"), None)
    if wheel_part and wheel_part.wheel_diameter is not None:
        effective_wheel_diameter = wheel_part.wheel_diameter
    else:
        effective_wheel_diameter = setup.wheel_diameter or trim.stock_wheel_diameter

    reasons: list[str] = []
    required_changes: list[str] = []
    conflicts: list[str] = []

    if setup.keep_current_wheels and wheel_part:
        reasons.append("This package requires changing the current wheel setup.")

    if budget_max and package.price_band.max > budget_max:
        reasons.append(
            f"Budget ceiling ${budget_max:,} is below the package ceiling of ${package.price_band.max:,}."
        )

    for rule in package.required_conditions:
        if rule.kind == "min_effective_wheel_diameter":
            required_min = int(rule.value or 0)
            if effective_wheel_diameter < required_min:
                reasons.append(
                    f"{rule.message} Current effective wheel is {effective_wheel_diameter}-inch."
                )
            else:
                required_changes.append(rule.message)
        elif rule.kind == "wheel_part_overrides_tire_diameter":
            required_changes.append(rule.message)

    for rule in package.blocked_conditions:
        if rule.kind == "winter_priority" and "winter" in selected_goals:
            reasons.append(rule.message)
        elif rule.kind == "winter_priority":
            conflicts.append(rule.message)

    if wheel_part and wheel_part.wheel_diameter and wheel_part.wheel_diameter != trim.stock_wheel_diameter:
        required_changes.append(
            f"Move from stock {trim.stock_wheel_diameter}-inch wheels to {wheel_part.wheel_diameter}-inch wheels."
        )

    matched_goals = [goal for goal in selected_goals if package.goal_biases.get(goal, 0.0) >= 0.7]
    if not matched_goals:
        matched_goals = selected_goals[:1] if selected_goals else ["daily"]

    fitment_confidence = _fitment_confidence(package, required_changes, conflicts)
    goal_alignment = _goal_score(package, selected_goals)
    cost_efficiency = _cost_efficiency(package, budget_max)
    safety_preservation = _safety_preservation(trim, package, parts)
    dependency_simplicity = _dependency_simplicity(package)
    conflict_penalty = round(0.08 * len(conflicts), 3)

    score_breakdown = ScoreBreakdown(
        goal_alignment=goal_alignment,
        fitment_confidence=fitment_confidence,
        cost_efficiency=cost_efficiency,
        safety_preservation=safety_preservation,
        dependency_simplicity=dependency_simplicity,
        conflict_penalty=conflict_penalty,
    )

    if reasons:
        return Evaluation(
            package=package,
            trim=trim,
            valid=False,
            reasons=reasons,
            matched_goals=matched_goals,
            required_changes=required_changes,
            conflicts=conflicts,
            score_breakdown=score_breakdown,
            final_score=0.0,
            fitment_confidence=fitment_confidence,
            effective_wheel_diameter=effective_wheel_diameter,
            parts=parts,
        )

    final_score = round(
        100
        * (
            (0.35 * goal_alignment)
            + (0.25 * fitment_confidence)
            + (0.15 * cost_efficiency)
            + (0.15 * safety_preservation)
            + (0.10 * dependency_simplicity)
            - conflict_penalty
        ),
        1,
    )

    return Evaluation(
        package=package,
        trim=trim,
        valid=True,
        reasons=[],
        matched_goals=matched_goals,
        required_changes=list(dict.fromkeys(required_changes + package.supporting_parts)),
        conflicts=list(dict.fromkeys(conflicts + package.tradeoff_notes)),
        score_breakdown=score_breakdown,
        final_score=final_score,
        fitment_confidence=fitment_confidence,
        effective_wheel_diameter=effective_wheel_diameter,
        parts=parts,
    )


def collect_package_evaluations(
    *,
    trim: VehicleTrim,
    selected_goals: list[str],
    budget_max: int | None,
    current_setup: CurrentSetup | None,
    repository: SeedRepository,
) -> tuple[list[Evaluation], list[Evaluation]]:
    valid: list[Evaluation] = []
    rejected: list[Evaluation] = []

    for package in repository.list_packages():
        evaluation = evaluate_package(
            trim=trim,
            package=package,
            selected_goals=selected_goals,
            budget_max=budget_max,
            current_setup=current_setup,
            repository=repository,
        )
        if evaluation.valid:
            valid.append(evaluation)
        else:
            rejected.append(evaluation)

    valid.sort(key=lambda item: item.final_score, reverse=True)
    rejected.sort(
        key=lambda item: (
            len(item.reasons),
            -(item.score_breakdown.goal_alignment if item.score_breakdown else 0),
        )
    )
    return valid, rejected


def build_recommendations(
    request: BuildRecommendationRequest,
    repository: SeedRepository | None = None,
) -> tuple[list[BuildRecommendation], list[Evaluation]]:
    repository = repository or get_repository()
    try:
        trim = repository.get_trim(request.trim_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown trim.") from exc

    selected_goals = list(
        dict.fromkeys(request.selected_goals or (request.query.goals if request.query else ["daily"]))
    )
    if not selected_goals:
        selected_goals = ["daily"]

    budget_max = request.budget_max or (request.query.budget_max if request.query else None)
    current_setup = request.current_setup or (request.query.current_setup if request.query else None)

    valid, rejected = collect_package_evaluations(
        trim=trim,
        selected_goals=selected_goals,
        budget_max=budget_max,
        current_setup=current_setup,
        repository=repository,
    )

    recommendations = [
        BuildRecommendation(
            package_id=item.package.package_id,
            title=item.package.title,
            subtitle=item.package.subtitle,
            description=item.package.description,
            score=item.final_score,
            score_breakdown=item.score_breakdown,
            matched_goals=item.matched_goals,
            required_changes=item.required_changes,
            conflicts=item.conflicts,
            cost_band=item.package.price_band,
            effect_tags=item.package.effect_tags,
            compatibility_status="Compatible" if not item.required_changes else "Compatible with supporting changes",
            fitment_confidence=item.fitment_confidence,
            safety_context={
                "safety_index": trim.safety_index,
                "recall_burden": trim.recall_burden,
                "complaint_burden": trim.complaint_burden,
                "recall_summary": trim.recall_summary,
                "complaint_summary": trim.complaint_summary,
                "seed_notice": "Demo snapshot values pending live NHTSA ingest.",
            },
            why_it_matched=[
                f"Goal alignment favors {', '.join(item.matched_goals)}." if item.matched_goals else "Strong daily fit.",
                f"Package stays within the {item.effective_wheel_diameter}-inch wheel path.",
                f"Estimated cost band lands at ${item.package.price_band.min:,}-${item.package.price_band.max:,}.",
            ],
            explanation=recommendation_explanation(
                trim=trim,
                package_title=item.package.title,
                matched_goals=item.matched_goals,
                why_it_matched=[
                    f"it matches {', '.join(item.matched_goals)}",
                    f"the fitment confidence is {item.fitment_confidence:.0%}",
                ],
                conflicts=item.conflicts,
                required_changes=item.required_changes,
            ),
            what_would_change=[
                "A bigger budget would unlock more aggressive wheel or brake packages."
                if budget_max
                else "Adding a budget cap would move cheaper packages upward.",
                "Switching to an 18-inch setup would unlock big brake options."
                if item.effective_wheel_diameter < 18
                else "Going back to 17-inch wheels would improve winter comfort.",
            ],
            graph_id=encode_graph_payload(
                {
                    "trim_id": trim.trim_id,
                    "package_id": item.package.package_id,
                    "selected_goals": selected_goals,
                    "budget_max": budget_max,
                    "current_setup": current_setup.model_dump() if current_setup else {},
                }
            ),
        )
        for item in valid[:5]
    ]

    return recommendations, rejected
