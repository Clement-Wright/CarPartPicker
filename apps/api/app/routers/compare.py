from __future__ import annotations

from fastapi import APIRouter

from app.schemas import CompareRequest, CompareResponse
from app.services.compare_service import compare_packages

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("", response_model=CompareResponse)
def compare_builds(request: CompareRequest) -> CompareResponse:
    return compare_packages(request.trim_id, request.package_ids)

