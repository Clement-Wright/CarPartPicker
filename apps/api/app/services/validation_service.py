from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import BuildState, BuildValidationSnapshot, ValidationSummary
from app.services.compatibility_service import run_interface_checks
from app.services.dependency_service import run_dependency_checks
from app.services.geometry_service import run_geometry_checks


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _summary(findings) -> ValidationSummary:
    summary = ValidationSummary()
    for finding in findings:
        if finding.severity == "BLOCKER":
            summary.blockers += 1
        elif finding.severity == "WARNING":
            summary.warnings += 1
        elif finding.severity == "SCENARIO_PENALTY":
            summary.scenario_penalties += 1
        elif finding.severity == "FABRICATION_REQUIRED":
            summary.fabrication_required += 1
        elif finding.severity == "UNKNOWN":
            summary.unknown += 1
    return summary


def build_validation_snapshot(build: BuildState, *, phase: str = "fast") -> BuildValidationSnapshot:
    findings = [
        *run_interface_checks(build),
        *run_geometry_checks(build, phase=phase),
        *run_dependency_checks(build, phase=phase),
    ]
    if phase == "heavy":
        findings.extend(
            finding.model_copy(update={"phase": "heavy"})
            for finding in findings
            if finding.phase == "fast" and finding.severity in {"WARNING", "SCENARIO_PENALTY"}
        )
    return BuildValidationSnapshot(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        phase=phase,
        summary=_summary(findings),
        findings=findings,
        computed_at=_now(),
    )
