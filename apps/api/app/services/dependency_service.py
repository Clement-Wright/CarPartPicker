from __future__ import annotations

from app.schemas import BuildState, ValidationFinding
from app.services.build_helpers import active_engine_family, selected_parts
from app.services.catalog_seed import prov
from app.services.engine_simulation_service import build_engine_simulation_snapshot


def run_dependency_checks(build: BuildState, *, phase: str = "fast") -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    parts = selected_parts(build)
    selected_ids = {item.part_id for item in parts.values()}
    engine_family = active_engine_family(build)
    dyno = build_engine_simulation_snapshot(build).dyno
    torque_estimate = dyno.peak_torque_lbft

    transmission_capacity = parts["transmission"].capabilities.get("torque_capacity", build.vehicle.driveline_limit_lbft)
    clutch_capacity = parts["clutch"].capabilities.get("torque_capacity", build.vehicle.driveline_limit_lbft)
    diff_capacity = parts["differential"].capabilities.get("torque_capacity", build.vehicle.driveline_limit_lbft)

    for subsystem, part in parts.items():
        for index, dep in enumerate(part.dependency_rules):
            if dep.kind == "requires_part" and dep.required_part_ids and not all(required in selected_ids for required in dep.required_part_ids):
                findings.append(
                    ValidationFinding(
                        finding_id=f"dependency-{subsystem}-{index}",
                        phase=phase,
                        category="dependency",
                        severity=dep.severity,
                        subsystem=subsystem,
                        title="Supporting subsystem required",
                        detail=dep.message,
                        blocking=dep.severity == "BLOCKER",
                        related_parts=[part.part_id, *dep.required_part_ids],
                        provenance=dep.provenance,
                    )
                )

            if dep.kind == "blocks_scenario" and build.active_scenario == "winter":
                findings.append(
                    ValidationFinding(
                        finding_id=f"dependency-{subsystem}-{index}",
                        phase=phase,
                        category="scenario",
                        severity="SCENARIO_PENALTY",
                        subsystem=subsystem,
                        title="Scenario mismatch",
                        detail=dep.message,
                        related_parts=[part.part_id],
                        provenance=dep.provenance,
                    )
                )

    for required_part_id in engine_family.required_supporting_part_ids:
        if required_part_id not in selected_ids:
            findings.append(
                ValidationFinding(
                    finding_id=f"dependency-engine-{required_part_id}",
                    phase=phase,
                    category="dependency",
                    severity="BLOCKER",
                    subsystem="engine",
                    title="Engine swap support missing",
                    detail=f"{engine_family.label} needs {required_part_id.replace('_', ' ')} support before the swap is considered valid.",
                    blocking=True,
                    related_parts=[required_part_id],
                    related_configs=[build.engine_build_spec.config_id],
                    provenance=prov("dependency_service", "engine family support requirement"),
                )
            )

    for fabrication in engine_family.fabrication_requirements:
        if not build.tolerances.allow_fabrication:
            findings.append(
                ValidationFinding(
                    finding_id=f"dependency-fabrication-{fabrication.fabrication_id}",
                    phase=phase,
                    category="dependency",
                    severity="FABRICATION_REQUIRED",
                    subsystem="engine",
                    title="Fabrication required",
                    detail=fabrication.detail,
                    related_configs=[build.engine_build_spec.config_id],
                    provenance=prov("dependency_service", "engine family fabrication requirement"),
                )
            )

    for subsystem, capacity in {"transmission": transmission_capacity, "clutch": clutch_capacity, "differential": diff_capacity}.items():
        if torque_estimate > capacity:
            findings.append(
                ValidationFinding(
                    finding_id=f"dependency-{subsystem}-torque-limit",
                    phase=phase,
                    category="dependency",
                    severity="BLOCKER" if subsystem != "differential" else "WARNING",
                    subsystem=subsystem,
                    title="Torque capacity exceeded",
                    detail=f"Estimated torque is {torque_estimate:.0f} lb-ft, which exceeds the selected {subsystem} capacity of {capacity:.0f} lb-ft.",
                    blocking=subsystem != "differential",
                    related_parts=[parts[subsystem].part_id],
                    provenance=prov("dependency_service", "driveline torque capacity heuristic"),
                )
            )

    return findings
