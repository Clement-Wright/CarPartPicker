from __future__ import annotations

from fastapi import APIRouter

from app.schemas import TargetSpecRequest, TargetSpecResponse
from app.services.target_spec_service import solve_target_spec

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/target-spec", response_model=TargetSpecResponse)
def target_spec_endpoint(request: TargetSpecRequest) -> TargetSpecResponse:
    return solve_target_spec(request)
