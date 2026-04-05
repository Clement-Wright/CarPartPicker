from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    app_name: str
    api_prefix: str
    cors_origins: tuple[str, ...]
    seed_dir: Path
    build_storage_mode: str
    postgres_url: str | None
    neo4j_uri: str | None
    neo4j_username: str | None
    neo4j_password: str | None
    redis_url: str | None
    opensearch_url: str | None
    s3_endpoint_url: str | None
    s3_bucket: str | None
    vpic_base_url: str


def _env(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    return default


@lru_cache
def get_settings() -> Settings:
    root_dir = Path(__file__).resolve().parents[3]
    cors_origins = tuple(
        origin.strip()
        for origin in _env(
            "CARPARTPICKER_CORS_ORIGINS",
            "CATAPULT_CORS_ORIGINS",
            default="http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    )
    return Settings(
        app_name="CarPartPicker Seed Platform API",
        api_prefix="/api",
        cors_origins=cors_origins,
        seed_dir=root_dir / "data" / "seed",
        build_storage_mode=_env("CARPARTPICKER_BUILD_STORAGE_MODE", default="auto") or "auto",
        postgres_url=_env("CARPARTPICKER_POSTGRES_URL", "CATAPULT_POSTGRES_URL"),
        neo4j_uri=_env("CARPARTPICKER_NEO4J_URI", "CATAPULT_NEO4J_URI"),
        neo4j_username=_env("CARPARTPICKER_NEO4J_USERNAME", "CATAPULT_NEO4J_USERNAME"),
        neo4j_password=_env("CARPARTPICKER_NEO4J_PASSWORD", "CATAPULT_NEO4J_PASSWORD"),
        redis_url=_env("CARPARTPICKER_REDIS_URL"),
        opensearch_url=_env("CARPARTPICKER_OPENSEARCH_URL"),
        s3_endpoint_url=_env("CARPARTPICKER_S3_ENDPOINT_URL"),
        s3_bucket=_env("CARPARTPICKER_S3_BUCKET"),
        vpic_base_url=_env(
            "CARPARTPICKER_VPIC_BASE_URL",
            "CATAPULT_VPIC_BASE_URL",
            default="https://vpic.nhtsa.dot.gov/api/vehicles",
        )
        or "https://vpic.nhtsa.dot.gov/api/vehicles",
    )

