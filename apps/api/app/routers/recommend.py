from __future__ import annotations

from fastapi import APIRouter

from app.schemas import BuildRecommendation, BuildRecommendationRequest
from app.services.recommendation_engine import build_recommendations

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.post("/builds", response_model=list[BuildRecommendation])
def recommend_builds(request: BuildRecommendationRequest) -> list[BuildRecommendation]:
    recommendations, _ = build_recommendations(request)
    return recommendations
