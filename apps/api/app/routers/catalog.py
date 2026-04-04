from __future__ import annotations

from fastapi import APIRouter

from app.schemas import VehicleSummary
from app.services.seed_repository import get_repository

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/trims", response_model=list[VehicleSummary])
def list_trims() -> list[VehicleSummary]:
    repository = get_repository()
    return [
        VehicleSummary(
            trim_id=trim.trim_id,
            label=f"{trim.year} {trim.make} {trim.model} {trim.trim}",
            stock_wheel_diameter=trim.stock_wheel_diameter,
            platform=trim.platform,
        )
        for trim in repository.list_trims()
    ]

