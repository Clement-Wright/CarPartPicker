from __future__ import annotations

from app.production_schemas import (
    AssemblyEdge,
    AssemblyNode,
    BuildAssemblyGraph,
    BuildSceneResponse,
    BuildValidationReport,
    SceneAssetStatus,
    SimulationResponse,
    SubsystemFitmentOutcome,
)
from app.schemas import BuildState
from app.services.build_helpers import selected_parts
from app.services.dyno_service import build_dyno_snapshot
from app.services.metrics_service import build_metric_snapshot
from app.services.production_mapper_service import seed_asset_readiness
from app.services.render_config_service import build_render_config
from app.services.scenario_service import build_scenario_snapshot
from app.services.validation_service import build_validation_snapshot
from app.services.vehicle_metrics_service import build_vehicle_metric_snapshot


def build_assembly_graph(build: BuildState) -> BuildAssemblyGraph:
    parts = selected_parts(build)
    nodes = [
        AssemblyNode(
            node_id="vehicle",
            kind="vehicle",
            subsystem="vehicle",
            label=f"{build.vehicle.year} {build.vehicle.make} {build.vehicle.model} {build.vehicle.trim}",
            selection_id=build.vehicle.trim_id,
        ),
        AssemblyNode(
            node_id="scenario",
            kind="scenario",
            subsystem="scenario",
            label=build.active_scenario.title(),
            selection_id=build.active_scenario,
        ),
        AssemblyNode(
            node_id="engine",
            kind="engine",
            subsystem="engine",
            label=build.engine_build_spec.label,
            selection_id=build.engine_build_spec.config_id,
        ),
    ]
    edges = [
        AssemblyEdge(
            edge_id="vehicle-scenario",
            source="vehicle",
            target="scenario",
            relation="scored_for",
            status="direct_fit",
        ),
        AssemblyEdge(
            edge_id="vehicle-engine",
            source="vehicle",
            target="engine",
            relation="configured_with",
            status="direct_fit",
        ),
    ]

    for selection in build.selections:
        if selection.subsystem == "engine" or selection.selected_part_id is None:
            continue
        node_id = f"part-{selection.subsystem}"
        nodes.append(
            AssemblyNode(
                node_id=node_id,
                kind="part",
                subsystem=selection.subsystem,
                label=parts[selection.subsystem].label,
                selection_id=selection.selected_part_id,
            )
        )
        edges.append(
            AssemblyEdge(
                edge_id=f"edge-{selection.subsystem}",
                source="vehicle" if selection.subsystem in {"body_aero", "suspension", "brakes", "wheels", "tires"} else "engine",
                target=node_id,
                relation="mounts_or_depends_on",
                status="direct_fit",
            )
        )

    return BuildAssemblyGraph(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        nodes=nodes,
        edges=edges,
    )


def _subsystem_outcome(build: BuildState, subsystem: str, reasons: list[str], blocking: bool, fabrication: bool) -> SubsystemFitmentOutcome:
    if blocking:
        outcome = "invalid"
    elif fabrication:
        outcome = "fits_with_fabrication"
    else:
        outcome = "direct_fit"

    selection_id = (
        build.engine_build_spec.config_id
        if subsystem == "engine"
        else next(
            (
                selection.selected_part_id
                for selection in build.selections
                if selection.subsystem == subsystem and selection.selected_part_id is not None
            ),
            None,
        )
    )
    label = build.engine_build_spec.label if subsystem == "engine" else selection_id or subsystem

    return SubsystemFitmentOutcome(
        subsystem=subsystem,
        selection_id=selection_id,
        outcome=outcome,
        asset_readiness=seed_asset_readiness(subsystem=subsystem, label=label),
        reasons=reasons,
    )


def build_validation_report(build: BuildState) -> BuildValidationReport:
    validation = build_validation_snapshot(build, phase="fast")
    grouped_reasons: dict[str, list[str]] = {}
    grouped_blocking: dict[str, bool] = {}
    grouped_fabrication: dict[str, bool] = {}

    for finding in validation.findings:
        grouped_reasons.setdefault(finding.subsystem, []).append(finding.title)
        grouped_blocking[finding.subsystem] = grouped_blocking.get(finding.subsystem, False) or finding.blocking or finding.severity == "BLOCKER"
        grouped_fabrication[finding.subsystem] = grouped_fabrication.get(finding.subsystem, False) or finding.severity == "FABRICATION_REQUIRED"

    subsystem_order = [slot.subsystem for slot in build.base_config.subsystem_slots]
    subsystem_outcomes = [
        _subsystem_outcome(
            build,
            subsystem,
            grouped_reasons.get(subsystem, []),
            grouped_blocking.get(subsystem, False),
            grouped_fabrication.get(subsystem, False),
        )
        for subsystem in subsystem_order
    ]

    production_blockers = []
    if validation.summary.blockers:
        production_blockers.append("Compatibility blockers remain unresolved.")
    production_blockers.extend(
        f"Exact asset readiness is incomplete for {item.subsystem}."
        for item in subsystem_outcomes
        if item.asset_readiness.status != "approved_exact"
    )
    production_blockers.append("Catalog and pricing remain in seed mode.")

    return BuildValidationReport(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        build=build,
        assembly_graph=build_assembly_graph(build),
        validation=validation,
        subsystem_outcomes=subsystem_outcomes,
        production_blockers=production_blockers,
    )


def build_scene_response(build: BuildState) -> BuildSceneResponse:
    render_config = build_render_config(build)
    selected = selected_parts(build)
    assets: list[SceneAssetStatus] = []

    for item in render_config.scene_objects:
        subsystem = item.slot if item.slot in selected else "engine" if item.slot == "engine_bay" else item.slot
        label = build.engine_build_spec.label if subsystem == "engine" else selected.get(subsystem).label if subsystem in selected else item.object_id
        assets.append(
            SceneAssetStatus(
                subsystem=subsystem,
                object_id=item.object_id,
                asset_readiness=seed_asset_readiness(subsystem=subsystem, label=label),
            )
        )

    return BuildSceneResponse(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        render_config=render_config,
        assets=assets,
    )


def simulate_build(build: BuildState, mode: str) -> SimulationResponse:
    if mode == "engine":
        snapshot = build_dyno_snapshot(build)
        payload = snapshot.model_dump()
    elif mode == "vehicle":
        snapshot = build_vehicle_metric_snapshot(build)
        payload = snapshot.model_dump()
    elif mode == "thermal":
        snapshot = build_vehicle_metric_snapshot(build)
        payload = {
            "thermal_headroom": snapshot.metrics.thermal_headroom,
            "driveline_stress": snapshot.metrics.driveline_stress,
            "comfort_index": snapshot.metrics.comfort_index,
        }
    elif mode == "braking":
        snapshot = build_metric_snapshot(build)
        payload = {
            "braking_distance_ft": snapshot.metrics.braking_distance_ft,
            "lateral_grip_g": snapshot.metrics.lateral_grip_g,
            "upgrade_cost_usd": snapshot.metrics.upgrade_cost_usd,
        }
    elif mode == "handling":
        snapshot = build_scenario_snapshot(build, scenario_name=build.active_scenario)
        payload = snapshot.model_dump()
    else:
        raise ValueError(f"Unsupported simulation mode: {mode}")

    return SimulationResponse(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        mode=mode,
        payload=payload,
    )
