from __future__ import annotations

from fastapi import APIRouter

from app.schemas import CatalogImportRequest, CatalogImportResponse
from app.services.catalog_ingest_service import import_seed_catalog

router = APIRouter(prefix="/catalog/import", tags=["catalog-import"])


@router.post("/seed", response_model=CatalogImportResponse)
def import_seed_endpoint(request: CatalogImportRequest) -> CatalogImportResponse:
    return import_seed_catalog(request)
