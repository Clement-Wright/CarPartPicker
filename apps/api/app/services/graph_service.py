from __future__ import annotations

from app.schemas import GraphEdge, GraphNode, GraphResponse
from app.services.build_helpers import active_engine_family, selected_parts
from app.services.build_state_service import get_build
from app.services.validation_service import build_validation_snapshot


def build_graph(build_id: str) -> GraphResponse:
    build = get_build(build_id)
    parts = selected_parts(build)
    engine_family = active_engine_family(build)
    validation = build_validation_snapshot(build, phase="fast")

    nodes = [
        GraphNode(
            id="vehicle",
            label=f"{build.vehicle.year} {build.vehicle.make} {build.vehicle.model}",
            kind="vehicle",
            status="positive",
            description=f"Base trim: {build.vehicle.trim}.",
            position={"x": 80, "y": 180},
        ),
        GraphNode(
            id="scenario",
            label=build.active_scenario.title(),
            kind="scenario",
            status="info",
            description="Active scenario definition.",
            position={"x": 340, "y": 60},
        ),
        GraphNode(
            id="engine",
            label=engine_family.label,
            kind="engine",
            status="warning" if build.engine_build_spec.engine_family_id != "fa24d_native" else "positive",
            description=f"Engine build spec: {build.engine_build_spec.label}.",
            position={"x": 340, "y": 160},
        ),
    ]
    edges = [
        GraphEdge(id="vehicle-scenario", source="vehicle", target="scenario", label="scored for", status="info"),
        GraphEdge(id="vehicle-engine", source="vehicle", target="engine", label="configured with", status="info"),
    ]

    y = 250
    for index, subsystem in enumerate([slot for slot in build.base_config.subsystem_slots if slot.subsystem != "engine"], start=1):
        part = parts[subsystem.subsystem]
        status = "positive"
        if any(part.part_id in finding.related_parts and finding.severity == "BLOCKER" for finding in validation.findings):
            status = "conflict"
        elif any(part.part_id in finding.related_parts for finding in validation.findings):
            status = "warning"

        node_id = f"part-{index}"
        nodes.append(
            GraphNode(
                id=node_id,
                label=part.label,
                kind=subsystem.subsystem,
                status=status,
                description=part.notes,
                position={"x": 340, "y": float(y)},
            )
        )
        edges.append(
            GraphEdge(
                id=f"edge-{index}",
                source="engine" if subsystem.subsystem in {"forced_induction", "intake", "exhaust", "cooling", "fuel_system", "tune"} else "vehicle",
                target=node_id,
                label=subsystem.subsystem.replace("_", " "),
                status=status,
            )
        )
        y += 78

    offset_y = 100
    highlights: list[str] = []
    findings: list[str] = []
    for idx, finding in enumerate(validation.findings, start=1):
        node_id = f"finding-{idx}"
        nodes.append(
            GraphNode(
                id=node_id,
                label=finding.title,
                kind=finding.category,
                status="conflict" if finding.severity == "BLOCKER" else "warning",
                description=finding.detail,
                position={"x": 700, "y": float(offset_y)},
            )
        )
        source_id = "engine" if finding.related_configs else next(
            (
                f"part-{part_index}"
                for part_index, subsystem in enumerate([slot for slot in build.base_config.subsystem_slots if slot.subsystem != "engine"], start=1)
                if parts[subsystem.subsystem].part_id in finding.related_parts
            ),
            "vehicle",
        )
        edges.append(
            GraphEdge(
                id=f"finding-edge-{idx}",
                source=source_id,
                target=node_id,
                label=finding.severity.lower(),
                status="conflict" if finding.severity == "BLOCKER" else "warning",
            )
        )
        highlights.append(finding.title)
        findings.append(finding.detail)
        offset_y += 84

    return GraphResponse(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        nodes=nodes,
        edges=edges,
        highlights=highlights,
        findings=findings,
    )
