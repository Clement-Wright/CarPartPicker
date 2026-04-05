from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.routers import builds, catalog, catalog_import, search, v1, vehicle, vin
from app.services.nhtsa_ingest import build_ingest_status

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    description="Seed-mode car builder API with a production-oriented v1 upgrade path.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "mode": "seed_mode",
        "build_storage_mode": settings.build_storage_mode,
        "integrations": {
            "postgres": bool(settings.postgres_url),
            "redis": bool(settings.redis_url),
            "opensearch": bool(settings.opensearch_url),
            "object_storage": bool(settings.s3_endpoint_url and settings.s3_bucket),
            "neo4j_legacy": bool(settings.neo4j_uri),
        },
        "ingest": build_ingest_status(),
    }


app.include_router(catalog.router, prefix=settings.api_prefix)
app.include_router(vehicle.router, prefix=settings.api_prefix)
app.include_router(vin.router, prefix=settings.api_prefix)
app.include_router(builds.router, prefix=settings.api_prefix)
app.include_router(search.router, prefix=settings.api_prefix)
app.include_router(catalog_import.router, prefix=settings.api_prefix)
app.include_router(v1.router, prefix=settings.api_prefix)
