from __future__ import annotations

import json

from app.services.nhtsa_ingest import build_ingest_status


def main() -> None:
    status = build_ingest_status()
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
