from __future__ import annotations

from pathlib import Path
import sys

import pytest


API_ROOT = Path(__file__).resolve().parents[2]

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


@pytest.fixture(autouse=True)
def reset_build_store_fixture() -> None:
    from app.services.build_storage_service import reset_build_store

    reset_build_store()
    yield
    reset_build_store()

