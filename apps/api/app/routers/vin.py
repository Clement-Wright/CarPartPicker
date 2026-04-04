from __future__ import annotations

from fastapi import APIRouter

from app.schemas import DecodeVinRequest, DecodedVehicle
from app.services.vin_service import decode_vin

router = APIRouter(prefix="/vin", tags=["vin"])


@router.post("/decode", response_model=DecodedVehicle)
async def decode_vehicle(request: DecodeVinRequest) -> DecodedVehicle:
    return await decode_vin(request.vin)

