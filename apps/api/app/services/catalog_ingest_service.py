from __future__ import annotations

from app.schemas import CatalogImportRequest, CatalogImportResponse
from app.services.catalog_seed import IMPORT_BATCHES


def import_seed_catalog(request: CatalogImportRequest) -> CatalogImportResponse:
    batch = IMPORT_BATCHES["seed_parts_2026q2"] if request.import_scope != "seed_engine_families" else IMPORT_BATCHES["seed_engine_2026q2"]
    if request.import_scope == "seed_all":
        batch = IMPORT_BATCHES["seed_parts_2026q2"]
    imported_entities = {
        "vehicle_platforms": 2 if request.import_scope in {"seed_all", "seed_parts"} else 0,
        "engine_families": 3 if request.import_scope in {"seed_all", "seed_engine_families"} else 0,
        "parts": 30 if request.import_scope in {"seed_all", "seed_parts"} else 0,
    }
    return CatalogImportResponse(
        import_batch=batch,
        imported_entities=imported_entities,
        notes=[
            "This is ingest scaffolding for the demo seed catalog.",
            "ACES/PIES-style import boundaries are modeled, but live licensed ingestion is intentionally deferred.",
        ],
    )
