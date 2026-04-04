from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import VehicleDetail
from app.services.seed_repository import get_repository

router = APIRouter(prefix="/vehicle", tags=["vehicle"])


@router.get("/{trim_id}", response_model=VehicleDetail)
def vehicle_detail(trim_id: str) -> VehicleDetail:
    repository = get_repository()
    try:
        trim = repository.get_trim(trim_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown trim.") from exc

    return VehicleDetail(
        trim=trim,
        safety_context={
            "safety_index": trim.safety_index,
            "recall_burden": trim.recall_burden,
            "complaint_burden": trim.complaint_burden,
            "recall_summary": trim.recall_summary,
            "complaint_summary": trim.complaint_summary,
            "seed_notice": "Demo snapshot values pending live NHTSA ingest.",
        },
    )

