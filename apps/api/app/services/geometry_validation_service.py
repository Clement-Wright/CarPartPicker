from __future__ import annotations

from app.schemas import BuildState, ValidationFinding
from app.services.geometry_service import run_geometry_checks


def validate_geometry(build: BuildState, *, phase: str = "fast") -> list[ValidationFinding]:
    return run_geometry_checks(build, phase=phase)
