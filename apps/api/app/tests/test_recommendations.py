from app.schemas import BuildRecommendationRequest, CurrentSetup, ParsedBuildQuery
from app.services.recommendation_engine import build_recommendations


def test_stock_17_rejects_bbk_core() -> None:
    request = BuildRecommendationRequest(
        trim_id="gr86_2022_base",
        query=ParsedBuildQuery(
            goals=["daily", "braking"],
            budget_max=2600,
            hard_constraints=[],
            current_setup=CurrentSetup(wheel_diameter=17, keep_current_wheels=False),
            confidence=0.9,
            extracted_terms=[],
        ),
        selected_goals=["daily", "braking"],
        budget_max=2600,
        current_setup=CurrentSetup(wheel_diameter=17, keep_current_wheels=False),
    )

    recommendations, rejected = build_recommendations(request)
    rejected_ids = {item.package.package_id: item.reasons[0] for item in rejected}

    assert "bbk_core_18_only" in rejected_ids
    assert "18-inch" in rejected_ids["bbk_core_18_only"]
    assert recommendations


def test_winter_package_outranks_street_package() -> None:
    request = BuildRecommendationRequest(
        trim_id="brz_2023_premium",
        query=ParsedBuildQuery(
            goals=["winter"],
            budget_max=2200,
            hard_constraints=[],
            current_setup=CurrentSetup(wheel_diameter=17, keep_current_wheels=False),
            confidence=0.9,
            extracted_terms=[],
        ),
        selected_goals=["winter"],
        budget_max=2200,
        current_setup=CurrentSetup(wheel_diameter=17, keep_current_wheels=False),
    )

    recommendations, _ = build_recommendations(request)

    assert recommendations[0].package_id == "winter_traction_17"
    assert all(item.package_id != "street_performance_18" for item in recommendations)

