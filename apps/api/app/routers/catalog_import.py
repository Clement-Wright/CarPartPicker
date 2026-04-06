from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.catalog_import_schemas import CatalogImportRunResponse, CatalogImportTriggerRequest
from app.schemas import CatalogImportRequest, CatalogImportResponse
from app.services.catalog_ingest_service import (
    get_catalog_import_run,
    import_seed_catalog,
    list_catalog_import_runs,
    reindex_catalog_documents,
    retry_catalog_import,
    trigger_catalog_import,
)

router = APIRouter(prefix="/catalog/import", tags=["catalog-import"])


@router.post("/seed", response_model=CatalogImportResponse)
def import_seed_endpoint(request: CatalogImportRequest) -> CatalogImportResponse:
    return import_seed_catalog(request)


@router.post("/runs", response_model=CatalogImportRunResponse)
def trigger_import_run_endpoint(request: CatalogImportTriggerRequest) -> CatalogImportRunResponse:
    return trigger_catalog_import(request)


@router.get("/runs", response_model=list[CatalogImportRunResponse])
def list_import_runs_endpoint() -> list[CatalogImportRunResponse]:
    return [response for run in list_catalog_import_runs() if (response := get_catalog_import_run(run.import_run_id)) is not None]


@router.get("/runs/{import_run_id}", response_model=CatalogImportRunResponse)
def get_import_run_endpoint(import_run_id: str) -> CatalogImportRunResponse:
    response = get_catalog_import_run(import_run_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Unknown import run.")
    return response


@router.post("/runs/{import_run_id}/retry", response_model=CatalogImportRunResponse)
def retry_import_run_endpoint(import_run_id: str) -> CatalogImportRunResponse:
    response = retry_catalog_import(import_run_id)
    if response is None:
        raise HTTPException(status_code=404, detail="Unknown import run.")
    return response


@router.post("/reindex")
def reindex_import_catalog_endpoint() -> dict[str, object]:
    counts = reindex_catalog_documents()
    return {"status": "ok", "counts": counts}
