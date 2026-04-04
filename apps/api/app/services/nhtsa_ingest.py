from __future__ import annotations

from datetime import datetime, timezone


def planned_nhtsa_sources() -> list[dict[str, str]]:
    return [
        {"dataset": "ratings", "schedule": "annual", "source": "Safercar_data.csv"},
        {"dataset": "recalls", "schedule": "daily", "source": "recallsByVehicle + flat files"},
        {"dataset": "complaints", "schedule": "daily", "source": "complaintsByVehicle + flat files"},
        {"dataset": "manufacturer_communications", "schedule": "daily", "source": "MFR_COMMS flat files"},
        {"dataset": "vpic", "schedule": "nightly", "source": "local decode cache + optional live fallback"},
    ]


def build_ingest_status() -> dict[str, object]:
    return {
        "status": "seed_mode",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources": planned_nhtsa_sources(),
    }
