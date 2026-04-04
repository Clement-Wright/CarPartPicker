from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import builds, catalog, catalog_import, search, vehicle, vin
from app.services.nhtsa_ingest import build_ingest_status

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="BuildState-first GR86/BRZ configurator and simulator API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "mode": "buildstate-seed",
        "ingest": build_ingest_status(),
    }


app.include_router(catalog.router, prefix=settings.api_prefix)
app.include_router(vehicle.router, prefix=settings.api_prefix)
app.include_router(vin.router, prefix=settings.api_prefix)
app.include_router(builds.router, prefix=settings.api_prefix)
app.include_router(search.router, prefix=settings.api_prefix)
app.include_router(catalog_import.router, prefix=settings.api_prefix)
