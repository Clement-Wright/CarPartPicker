from __future__ import annotations

from fastapi import HTTPException
import httpx

from app.config import get_settings
from app.schemas import DecodedVehicle
from app.services.seed_repository import SeedRepository, get_repository


async def decode_vin(vin: str, repository: SeedRepository | None = None) -> DecodedVehicle:
    repository = repository or get_repository()
    sanitized = vin.strip().upper()
    if len(sanitized) != 17:
        raise HTTPException(status_code=422, detail="VIN must be 17 characters.")

    cached = repository.lookup_vin(sanitized)
    if cached:
        return cached

    settings = get_settings()
    url = f"{settings.vpic_base_url}/DecodeVinValues/{sanitized}?format=json"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=404,
            detail="VIN not found in local cache and live vPIC lookup is unavailable.",
        ) from exc

    results = payload.get("Results") or []
    if not results:
        raise HTTPException(status_code=404, detail="VIN could not be decoded.")

    result = results[0]
    year = int(result["ModelYear"]) if result.get("ModelYear") else None
    make = result.get("Make") or None
    model = result.get("Model") or None
    trim_name = result.get("Trim") or None
    matched_trim = repository.find_trim_by_vehicle(year=year, make=make, model=model, trim=trim_name)

    return DecodedVehicle(
        vin=sanitized,
        trim_id=matched_trim.trim_id if matched_trim else None,
        year=year,
        make=make,
        model=model,
        trim=matched_trim.trim if matched_trim else trim_name,
        source="vpic_live",
        cache_hit=False,
    )

