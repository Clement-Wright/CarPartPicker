from __future__ import annotations

from collections import Counter

from app.production_schemas import (
    AssemblyEdge,
    AssemblyNode,
    BuildAssemblyGraph,
    BuildSceneResponse,
    BuildValidationReport,
    OmittedSceneItem,
    ProxyGeometry,
    ReadinessNote,
    SceneAnchor,
    SceneDimensions,
    SceneHighlight,
    SceneItem,
    SceneSummary,
    SceneTransform,
    SimulationResponse,
    SubsystemFitmentOutcome,
    VisualizationSummary,
)
from app.schemas import BuildDynoSnapshot, BuildState, RenderSceneObject
from app.services.build_helpers import active_engine_family, selected_parts
from app.services.compatibility_engine_service import build_compatibility_diagnostics
from app.services.dyno_service import build_dyno_snapshot
from app.services.engine_editor_service import build_engine_editor_response
from app.services.metrics_service import build_metric_snapshot
from app.services.production_mapper_service import VisualizationProfile, describe_part_visualization
from app.services.render_config_service import build_render_config
from app.services.seed_repository import get_repository
from app.services.scenario_service import build_scenario_snapshot
from app.services.simulation_dataset_service import calibration_state_for_mode
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


def _engine_visualization(build: BuildState) -> VisualizationProfile:
    engine_family = active_engine_family(build)
    dimensions = SceneDimensions(
        length_mm=engine_family.envelope.length_mm,
        width_mm=engine_family.envelope.width_mm,
        height_mm=engine_family.envelope.height_mm,
    )
    return VisualizationProfile(
        mode="proxy_from_dimensions",
        has_exact_mesh=False,
        has_proxy_geometry=True,
        has_dimensional_specs=True,
        scene_renderable=True,
        catalog_visible=True,
        anchor_slot="engine_bay",
        proxy_geometry=ProxyGeometry(
            kind="box",
            color="#7e8c97" if engine_family.engine_family_id == "fa24d_native" else "#ff7b31",
            size_mm=(dimensions.length_mm, dimensions.height_mm, dimensions.width_mm),
        ),
        dimensions=dimensions,
        mesh_url=None,
        notes=[
            ReadinessNote(
                code="engine-proxy",
                message=f"{engine_family.label} is rendered as a dimensional engine envelope until an exact mesh is attached.",
            )
        ],
    )


def _profile_for_subsystem(build: BuildState, subsystem: str) -> tuple[str | None, VisualizationProfile]:
    repository = get_repository()
    if subsystem == "engine":
        return build.engine_build_spec.config_id, _engine_visualization(build)

    for selection in build.selections:
        if selection.subsystem == subsystem and selection.selected_part_id is not None:
            return selection.selected_part_id, describe_part_visualization(selected_parts(build, repository=repository)[subsystem], repository=repository)

    return None, VisualizationProfile(
        mode="unsupported",
        has_exact_mesh=False,
        has_proxy_geometry=False,
        has_dimensional_specs=False,
        scene_renderable=False,
        catalog_visible=False,
        anchor_slot=subsystem,
        proxy_geometry=None,
        dimensions=SceneDimensions(),
        mesh_url=None,
        notes=[
            ReadinessNote(
                code="missing-selection",
                message="No selection is active for this subsystem.",
            )
        ],
    )


def _build_visualization_summary(outcomes: list[SubsystemFitmentOutcome]) -> VisualizationSummary:
    counts = Counter(item.visualization_mode for item in outcomes)
    return VisualizationSummary(
        exact_mesh_ready=counts["exact_mesh_ready"],
        proxy_from_dimensions=counts["proxy_from_dimensions"],
        catalog_only=counts["catalog_only"],
        unsupported=counts["unsupported"],
        renderable_count=sum(1 for item in outcomes if item.scene_renderable),
        catalog_visible_count=sum(1 for item in outcomes if item.catalog_visible),
    )


def _subsystem_outcome(build: BuildState, subsystem: str, reasons: list[str], blocking: bool, fabrication: bool) -> SubsystemFitmentOutcome:
    if blocking:
        outcome = "invalid"
    elif fabrication:
        outcome = "fits_with_fabrication"
    else:
        outcome = "direct_fit"

    selection_id, profile = _profile_for_subsystem(build, subsystem)
    return SubsystemFitmentOutcome(
        subsystem=subsystem,
        selection_id=selection_id,
        outcome=outcome,
        visualization_mode=profile.mode,
        scene_renderable=profile.scene_renderable,
        catalog_visible=profile.catalog_visible,
        reasons=reasons,
        support_notes=profile.notes,
    )


def build_validation_report(build: BuildState) -> BuildValidationReport:
    repository = get_repository()
    validation = build_validation_snapshot(build, phase="fast")
    diagnostics, stages = build_compatibility_diagnostics(build)
    grouped_reasons: dict[str, list[str]] = {}
    grouped_blocking: dict[str, bool] = {}
    grouped_fabrication: dict[str, bool] = {}

    for diagnostic in diagnostics:
        grouped_reasons.setdefault(diagnostic.subsystem, []).append(diagnostic.error_code)
        grouped_blocking[diagnostic.subsystem] = grouped_blocking.get(diagnostic.subsystem, False) or diagnostic.severity == "error"
        grouped_fabrication[diagnostic.subsystem] = grouped_fabrication.get(diagnostic.subsystem, False) or diagnostic.severity == "fabrication"

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
    visualization_summary = _build_visualization_summary(subsystem_outcomes)

    support_notes = [
        "Visualization coverage does not change whether a part is mechanically valid, priced, or simulated.",
        "Compatibility diagnostics are evaluated in keyed, dimensional, systems, and dependency stages against the canonical build state.",
    ]
    if visualization_summary.catalog_only:
        support_notes.append("Some selected parts are specs-only and will be omitted from the 3D scene while remaining fully active in the build.")
    if visualization_summary.proxy_from_dimensions:
        support_notes.append("Dimension-driven proxy geometry is active for selected major assemblies until exact meshes are available.")

    return BuildValidationReport(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        source_mode="licensed" if repository.get_vehicle_record(build.vehicle.trim_id) is not None else "seed",
        build=build,
        assembly_graph=build_assembly_graph(build),
        validation=validation,
        compatibility_diagnostics=diagnostics,
        compatibility_stages=stages,
        subsystem_outcomes=subsystem_outcomes,
        visualization_summary=visualization_summary,
        support_notes=support_notes,
    )


def _transform_from_scene_object(item: RenderSceneObject) -> SceneTransform:
    return SceneTransform(position=item.position, rotation=item.rotation, scale=item.scale)


def _scene_item_from_object(
    *,
    part_id: str,
    instance_id: str,
    subsystem: str,
    asset_mode: str,
    proxy_geometry: ProxyGeometry | None,
    dimensions: SceneDimensions,
    anchor_slot: str | None,
    scene_object: RenderSceneObject,
) -> SceneItem:
    return SceneItem(
        part_id=part_id,
        instance_id=instance_id,
        subsystem=subsystem,
        asset_mode=asset_mode,
        proxy_geometry=proxy_geometry,
        dimensions=dimensions,
        transform=_transform_from_scene_object(scene_object),
        anchor=SceneAnchor(slot=anchor_slot or scene_object.slot, zone=subsystem),
    )


def _fallback_scene_object(part_id: str, subsystem: str, dimensions: SceneDimensions) -> RenderSceneObject:
    return RenderSceneObject(
        object_id=part_id,
        slot=subsystem,
        kind="proxy",
        color="#9aa8b3",
        position=(0.0, max(dimensions.height_mm / 2000, 0.12), 0.0),
        scale=(1.0, 1.0, 1.0),
        rotation=(0.0, 0.0, 0.0),
        visible=True,
    )


def _wheel_corner_objects(render_config_objects: list[RenderSceneObject]) -> list[RenderSceneObject]:
    return [item for item in render_config_objects if item.slot in {"front_left", "front_right", "rear_left", "rear_right"}]


def _generate_tire_scene_objects(build: BuildState, wheel_objects: list[RenderSceneObject]) -> list[RenderSceneObject]:
    tire_selection = next(
        (selection for selection in build.selections if selection.subsystem == "tires" and selection.selected_part_id is not None),
        None,
    )
    if tire_selection is None:
        return []

    if wheel_objects:
        return [
            RenderSceneObject(
                object_id=f"{tire_selection.selected_part_id}-{wheel.slot}",
                slot=wheel.slot,
                kind="tire",
                color="#15181c",
                position=wheel.position,
                scale=wheel.scale,
                rotation=wheel.rotation,
                visible=True,
                highlight=wheel.highlight,
            )
            for wheel in wheel_objects
        ]

    return [
        RenderSceneObject(
            object_id=f"{tire_selection.selected_part_id}-{corner}",
            slot=corner,
            kind="tire",
            color="#15181c",
            position=position,
            scale=(1.0, 1.0, 1.0),
            rotation=(0.0, 0.0, 0.0),
            visible=True,
        )
        for corner, position in (
            ("front_left", (-0.82, -0.3, 1.05)),
            ("front_right", (0.82, -0.3, 1.05)),
            ("rear_left", (-0.82, -0.3, -1.05)),
            ("rear_right", (0.82, -0.3, -1.05)),
        )
    ]


def build_scene_response(build: BuildState) -> BuildSceneResponse:
    repository = get_repository()
    render_config = build_render_config(build)
    selected = selected_parts(build, repository=repository)
    objects = list(render_config.scene_objects)
    wheel_objects = _wheel_corner_objects(objects)
    objects.extend(_generate_tire_scene_objects(build, wheel_objects))
    objects_by_part: dict[str, list[RenderSceneObject]] = {}

    for item in objects:
        part_key = item.object_id.split("-front_")[0].split("-rear_")[0]
        objects_by_part.setdefault(part_key, []).append(item)

    items: list[SceneItem] = []
    omitted_items: list[OmittedSceneItem] = []

    for selection in build.selections:
        if selection.selected_part_id is None:
            continue
        part = selected[selection.subsystem]
        profile = describe_part_visualization(part, repository=repository)

        if not profile.scene_renderable:
            omitted_items.append(
                OmittedSceneItem(
                    part_id=part.part_id,
                    subsystem=part.subsystem,
                    asset_mode=profile.mode,
                    hidden_reason=profile.notes[0].message,
                )
            )
            continue

        scene_objects = objects_by_part.get(part.part_id)
        if not scene_objects and part.subsystem == "tires":
            scene_objects = [item for item in objects if item.object_id.startswith(f"{part.part_id}-")]
        if not scene_objects:
            scene_objects = [_fallback_scene_object(part.part_id, part.subsystem, profile.dimensions)]

        for scene_object in scene_objects:
            items.append(
                _scene_item_from_object(
                    part_id=part.part_id,
                    instance_id=scene_object.object_id,
                    subsystem=part.subsystem,
                    asset_mode=profile.mode,
                    proxy_geometry=profile.proxy_geometry,
                    dimensions=profile.dimensions,
                    anchor_slot=profile.anchor_slot,
                    scene_object=scene_object,
                )
            )

    engine_profile = _engine_visualization(build)
    for scene_object in [item for item in render_config.scene_objects if item.slot in {"engine_bay", "intercooler"}]:
        items.append(
            _scene_item_from_object(
                part_id=build.engine_build_spec.engine_family_id,
                instance_id=scene_object.object_id,
                subsystem="engine",
                asset_mode=engine_profile.mode,
                proxy_geometry=engine_profile.proxy_geometry,
                dimensions=engine_profile.dimensions,
                anchor_slot=engine_profile.anchor_slot,
                scene_object=scene_object,
            )
        )

    summary = SceneSummary(
        renderable_count=len(items),
        exact_count=sum(1 for item in items if item.asset_mode == "exact_mesh_ready"),
        proxy_count=sum(1 for item in items if item.asset_mode == "proxy_from_dimensions"),
        omitted_count=len(omitted_items),
    )

    return BuildSceneResponse(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        source_mode="licensed" if repository.get_vehicle_record(build.vehicle.trim_id) is not None else "seed",
        items=items,
        omitted_items=omitted_items,
        highlights=[SceneHighlight(zone=item.zone, severity=item.severity, message=item.message) for item in render_config.highlights],
        summary=summary,
    )


def build_engine_editor(build: BuildState):
    return build_engine_editor_response(build)


def _simulation_source_mode(build: BuildState) -> str:
    repository = get_repository()
    return "licensed" if repository.get_vehicle_record(build.vehicle.trim_id) is not None else "seed"


def _build_thermal_payload(build: BuildState) -> dict[str, object]:
    engine_snapshot = build_dyno_snapshot(build)
    vehicle_snapshot = build_vehicle_metric_snapshot(build)
    derived = engine_snapshot.derived_values
    cooling_factor = float(derived.get("cooling_limit_factor_min", 1.0))
    charge_temp_factor = float(derived.get("charge_temp_limit_factor_min", 1.0))

    warnings = list(engine_snapshot.warnings)
    if cooling_factor < 0.94 and not any(item.get("code") == "coolant_headroom_low" for item in warnings):
        warnings.append(
            {
                "code": "coolant_headroom_low",
                "severity": "warning",
                "message": "Cooling demand is close to or above the calibrated rejection threshold.",
            }
        )
    if charge_temp_factor < 0.97 and not any(item.get("code") == "charge_temp_high" for item in warnings):
        warnings.append(
            {
                "code": "charge_temp_high",
                "severity": "warning",
                "message": "Charge temperature is elevated enough to threaten repeatable power.",
            }
        )
    if min(cooling_factor, charge_temp_factor) < 0.98:
        warnings.append(
            {
                "code": "power_derated_for_temperature",
                "severity": "warning",
                "message": "The engine model is applying a temperature-based power derate.",
            }
        )

    return {
        "engine_spec_hash": engine_snapshot.spec_hash,
        "model_version": engine_snapshot.model_version,
        "charge_temp_c": derived.get("charge_temp_c_peak"),
        "effective_boost_psi": derived.get("effective_boost_psi_peak"),
        "cooling_capacity_kw": derived.get("cooling_capacity_kw"),
        "cooling_demand_kw": derived.get("cooling_demand_kw_peak"),
        "coolant_headroom_ratio": round(cooling_factor, 3),
        "thermal_headroom": vehicle_snapshot.metrics.thermal_headroom,
        "power_derated_for_temperature": min(cooling_factor, charge_temp_factor) < 0.98,
        "warnings": warnings,
        "limiting_factors": engine_snapshot.limiting_factors,
        "explanation_summary": engine_snapshot.explanation_summary,
    }


def _simulation_calibration_state(build: BuildState, *, mode: str, source_mode: str, engine_snapshot: BuildDynoSnapshot | None = None) -> str:
    if source_mode == "seed":
        return "seed_heuristic"
    if mode not in {"engine", "vehicle", "thermal"}:
        return "calibration_required"
    if engine_snapshot is None:
        return calibration_state_for_mode(
            source_mode=source_mode,
            vehicle_id=build.vehicle.trim_id,
            engine_family_id=build.engine_build_spec.engine_family_id,
            drivetrain_config_id=build.drivetrain_config.config_id,
            mode=mode,
        )
    return "calibrated" if engine_snapshot.derived_values.get("reference_calibrated") else "calibration_required"


def simulate_build(build: BuildState, mode: str) -> SimulationResponse:
    source_mode = _simulation_source_mode(build)
    calibration_state = calibration_state_for_mode(
        source_mode=source_mode,
        vehicle_id=build.vehicle.trim_id,
        engine_family_id=build.engine_build_spec.engine_family_id,
        drivetrain_config_id=build.drivetrain_config.config_id,
        mode=mode,
    )

    if mode == "engine":
        snapshot = build_dyno_snapshot(build)
        calibration_state = _simulation_calibration_state(
            build,
            mode=mode,
            source_mode=source_mode,
            engine_snapshot=snapshot,
        )
        payload = snapshot.model_dump()
    elif mode == "vehicle":
        snapshot = build_vehicle_metric_snapshot(build)
        engine_snapshot = build_dyno_snapshot(build)
        calibration_state = _simulation_calibration_state(
            build,
            mode=mode,
            source_mode=source_mode,
            engine_snapshot=engine_snapshot,
        )
        payload = snapshot.model_dump()
        payload["engine_spec_hash"] = engine_snapshot.spec_hash
        payload["model_version"] = engine_snapshot.model_version
        payload["integration_summary"] = {
            "launch_controlled_by": "traction_limit" if snapshot.metrics.zero_to_sixty_s < 5.2 else "available_wheel_force",
            "top_speed_controlled_by": "drag_balance",
        }
    elif mode == "thermal":
        engine_snapshot = build_dyno_snapshot(build)
        calibration_state = _simulation_calibration_state(
            build,
            mode=mode,
            source_mode=source_mode,
            engine_snapshot=engine_snapshot,
        )
        payload = _build_thermal_payload(build)
    elif mode == "braking":
        snapshot = build_metric_snapshot(build)
        payload = {
            "braking_distance_ft": snapshot.metrics.braking_distance_ft,
            "lateral_grip_g": snapshot.metrics.lateral_grip_g,
            "upgrade_cost_usd": snapshot.metrics.upgrade_cost_usd,
            "estimate_message": "Braking remains a lower-fidelity estimate until dedicated brake and tire calibration data is added.",
        }
    elif mode == "handling":
        snapshot = build_scenario_snapshot(build, scenario_name=build.active_scenario)
        payload = snapshot.model_dump()
        payload["estimate_message"] = "Handling remains a scenario-weighted estimate until a calibrated chassis model lands."
    else:
        raise ValueError(f"Unsupported simulation mode: {mode}")

    return SimulationResponse(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        mode=mode,
        source_mode=source_mode,  # type: ignore[arg-type]
        calibration_state=calibration_state,  # type: ignore[arg-type]
        payload=payload,
    )
