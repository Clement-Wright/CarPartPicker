from __future__ import annotations

from fastapi import HTTPException

from app.schemas import ComparePackageSummary, CompareResponse
from app.services.explanation_service import compare_explanation
from app.services.recommendation_engine import evaluate_package
from app.services.seed_repository import SeedRepository, get_repository


AXES = ["safety", "fun", "utility", "cost", "mod_potential", "winter"]


def compare_packages(trim_id: str, package_ids: list[str], repository: SeedRepository | None = None) -> CompareResponse:
    repository = repository or get_repository()
    try:
        trim = repository.get_trim(trim_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown trim.") from exc

    summaries: list[ComparePackageSummary] = []

    for package_id in package_ids:
        try:
            package = repository.get_package(package_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown package {package_id}.") from exc

        evaluation = evaluate_package(
            trim=trim,
            package=package,
            selected_goals=["daily"],
            budget_max=None,
            current_setup=None,
            repository=repository,
        )
        summaries.append(
            ComparePackageSummary(
                package_id=package.package_id,
                title=package.title,
                subtitle=package.subtitle,
                axes=package.axes,
                cost_band=package.price_band,
                fitment_confidence=evaluation.fitment_confidence,
                effect_tags=package.effect_tags,
                tradeoffs=package.tradeoff_notes,
            )
        )

    baseline = summaries[0]
    deltas = {
        summary.package_id: {
            axis: round(getattr(summary.axes, axis) - getattr(baseline.axes, axis), 2)
            for axis in AXES
        }
        for summary in summaries[1:]
    }

    strongest_primary = max(AXES, key=lambda axis: getattr(baseline.axes, axis))
    challenger = summaries[1]
    strongest_challenger = max(AXES, key=lambda axis: getattr(challenger.axes, axis))

    return CompareResponse(
        axes=AXES,
        package_summaries=summaries,
        deltas=deltas,
        explanation_facts={
            "summary": compare_explanation(
                baseline.title,
                strongest_primary.replace("_", " "),
                challenger.title,
                strongest_challenger.replace("_", " "),
            ),
            "baseline": baseline.title,
            "challenger": challenger.title,
        },
    )

