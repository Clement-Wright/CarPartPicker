from __future__ import annotations

from app.schemas import BuildState, ValidationFinding
from app.services.compatibility_service import run_interface_checks


def validate_interfaces(build: BuildState) -> list[ValidationFinding]:
    return run_interface_checks(build)
