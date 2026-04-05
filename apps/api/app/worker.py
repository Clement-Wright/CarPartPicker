from __future__ import annotations

import json

from app.config import get_settings
from app.services.nhtsa_ingest import build_ingest_status


def main() -> None:
    settings = get_settings()
    status = build_ingest_status()
    print(
        json.dumps(
            {
                "worker_mode": "seed_scaffold",
                "build_storage_mode": settings.build_storage_mode,
                "redis_configured": bool(settings.redis_url),
                "opensearch_configured": bool(settings.opensearch_url),
                "object_storage_configured": bool(settings.s3_endpoint_url and settings.s3_bucket),
                "ingest": status,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
