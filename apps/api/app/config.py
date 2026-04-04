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
    postgres_url: str | None
    neo4j_uri: str | None
    neo4j_username: str | None
    neo4j_password: str | None
    vpic_base_url: str


@lru_cache
def get_settings() -> Settings:
    root_dir = Path(__file__).resolve().parents[3]
    cors_origins = tuple(
        origin.strip()
        for origin in os.getenv(
            "CATAPULT_CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    )
    return Settings(
        app_name="Catapult Build Graph Planner API",
        api_prefix="/api",
        cors_origins=cors_origins,
        seed_dir=root_dir / "data" / "seed",
        postgres_url=os.getenv("CATAPULT_POSTGRES_URL"),
        neo4j_uri=os.getenv("CATAPULT_NEO4J_URI"),
        neo4j_username=os.getenv("CATAPULT_NEO4J_USERNAME"),
        neo4j_password=os.getenv("CATAPULT_NEO4J_PASSWORD"),
        vpic_base_url=os.getenv(
            "CATAPULT_VPIC_BASE_URL",
            "https://vpic.nhtsa.dot.gov/api/vehicles",
        ),
    )

