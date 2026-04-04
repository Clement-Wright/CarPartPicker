from __future__ import annotations

from app.schemas import BuildDynoSnapshot, BuildState
from app.services.engine_simulation_service import build_engine_simulation_snapshot


def build_dyno_snapshot(build: BuildState) -> BuildDynoSnapshot:
    return build_engine_simulation_snapshot(build)
