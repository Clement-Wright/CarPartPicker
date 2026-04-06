from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4

from fastapi import HTTPException

from app.schemas import (
    BuildComputationVersion,
    BuildDetailResponse,
    BuildState,
    BuildSubsystemSelection,
    CloneBuildResponse,
    CreateBuildRequest,
    PatchBuildPartsRequest,
    PatchDrivetrainRequest,
    PatchEngineRequest,
    PresetApplicationResponse,
)
from app.services.seed_repository import CatalogRepository, get_repository
from app.services.simulation_dataset_service import default_engine_spec_updates
from app.services.build_storage_service import get_build_store


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _selection_token(item: BuildSubsystemSelection) -> str:
    return f"{item.subsystem}:{item.selected_part_id or '-'}:{item.selected_config_id or '-'}:{item.source}"


def _build_hash(build: BuildState) -> str:
    payload = "|".join(
        [
            build.vehicle.trim_id,
            build.active_scenario,
            str(build.target_metrics.model_dump()),
            str(build.tolerances.model_dump()),
            *( _selection_token(item) for item in sorted(build.selections, key=lambda s: s.subsystem)),
            str(build.engine_build_spec.model_dump()),
            str(build.drivetrain_config.model_dump()),
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()[:16]


def _normalize_build(build: BuildState) -> BuildState:
    build_hash = _build_hash(build)
    revision = build.computation.revision + 1 if build.computation else 1
    return build.model_copy(
        update={
            "computation": BuildComputationVersion(
                build_hash=build_hash,
                revision=revision,
                updated_at=_now(),
            )
        }
    )


def _new_selection(subsystem: str, *, part_id: str | None = None, config_id: str | None = None, source: str = "stock") -> BuildSubsystemSelection:
    return BuildSubsystemSelection(
        subsystem=subsystem,
        selected_part_id=part_id,
        selected_config_id=config_id,
        source=source,
    )


def create_build(request: CreateBuildRequest, repository: CatalogRepository | None = None) -> BuildState:
    repository = repository or get_repository()
    trim_id = request.trim_id
    if request.vin and not trim_id:
        decoded = repository.lookup_vin(request.vin)
        if not decoded or not decoded.trim_id:
            raise HTTPException(status_code=404, detail="VIN not found in the demo cache.")
        trim_id = decoded.trim_id
    if not trim_id:
        raise HTTPException(status_code=422, detail="Provide a trim_id or VIN to create a build.")

    try:
        trim = repository.get_trim(trim_id)
        base_config = repository.get_base_config(trim_id)
        platform = repository.get_platform(trim.platform)
        chassis_envelope = repository.get_chassis_envelope(trim.platform)
        engine_config = repository.get_default_engine_config(trim_id)
        drivetrain_config = repository.get_default_drivetrain_config(trim_id)
        repository.get_scenario(request.scenario_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown trim or scenario.") from exc

    selections: list[BuildSubsystemSelection] = [
        _new_selection(subsystem="engine", config_id=engine_config.config_id)
    ]
    selections.extend(
        _new_selection(subsystem=slot.subsystem, part_id=slot.stock_part_id)
        for slot in base_config.subsystem_slots
        if slot.subsystem != "engine" and slot.stock_part_id
    )

    build = BuildState(
        build_id=str(uuid4()),
        vehicle=trim,
        vehicle_platform=platform,
        chassis_envelope=chassis_envelope,
        base_config=base_config,
        active_scenario=request.scenario_name,
        target_metrics=request.target_metrics,
        tolerances=request.tolerances,
        selections=selections,
        engine_build_spec=engine_config,
        drivetrain_config=drivetrain_config,
        computation=BuildComputationVersion(build_hash="", revision=0, updated_at=_now()),
        active_notes=["Build created from stock base configuration."],
    )
    build = _normalize_build(build)

    return get_build_store().save(build)


def get_build(build_id: str) -> BuildState:
    build = get_build_store().get(build_id)
    if build is None:
        raise HTTPException(status_code=404, detail="Unknown build id.")
    return build


def patch_build(build_id: str, request: PatchBuildPartsRequest, repository: CatalogRepository | None = None) -> BuildState:
    repository = repository or get_repository()
    build = get_build(build_id)
    selections = {item.subsystem: item.model_copy(deep=True) for item in build.selections}

    for subsystem, part_id in request.parts.items():
        if subsystem == "engine":
            raise HTTPException(status_code=422, detail="Use /engine to update the engine build spec.")
        if subsystem not in selections:
            raise HTTPException(status_code=422, detail=f"Unknown subsystem: {subsystem}")
        part = repository.get_part(part_id)
        if part.subsystem != subsystem:
            raise HTTPException(status_code=422, detail=f"Part {part_id} does not belong to subsystem {subsystem}.")
        selections[subsystem] = _new_selection(subsystem=subsystem, part_id=part_id, source="manual")

    active_scenario = request.scenario_name or build.active_scenario
    repository.get_scenario(active_scenario)

    updated = build.model_copy(
        update={
            "active_scenario": active_scenario,
            "target_metrics": request.target_metrics or build.target_metrics,
            "tolerances": request.tolerances or build.tolerances,
            "selections": [selections[subsystem] for subsystem in [slot.subsystem for slot in build.base_config.subsystem_slots]],
            "active_notes": ["Build updated via subsystem patch."],
        }
    )
    updated = _normalize_build(updated)
    return get_build_store().save(updated)


def patch_engine(build_id: str, request: PatchEngineRequest, repository: CatalogRepository | None = None) -> BuildState:
    repository = repository or get_repository()
    build = get_build(build_id)
    engine_spec = build.engine_build_spec.model_copy(deep=True)

    if request.engine_family_id and request.engine_family_id != engine_spec.engine_family_id:
        family = repository.get_engine_family(request.engine_family_id)
        engine_spec = engine_spec.model_copy(
            update={
                "config_id": f"engine_cfg_{family.engine_family_id}_{uuid4().hex[:6]}",
                "engine_family_id": family.engine_family_id,
                "label": family.label,
                "cylinder_count": family.architecture.cylinder_count,
                "layout": family.architecture.layout,
                "bore_mm": family.stock_bore_mm,
                "stroke_mm": family.stock_stroke_mm,
                "compression_ratio": family.compression_ratio,
                "valve_train": engine_spec.valve_train.model_copy(
                    update={"valves_per_cylinder": family.architecture.valves_per_cylinder}
                ),
                "induction": engine_spec.induction.model_copy(
                    update={"type": "turbo" if "turbo" in family.tags else "na", "boost_psi": 18.0 if "turbo" in family.tags else 0.0}
                ),
                "rev_limit_rpm": family.base_redline_rpm,
            }
        )
        engine_spec = engine_spec.model_copy(update=default_engine_spec_updates(engine_family=family))

    if request.label is not None:
        engine_spec.label = request.label
    if request.cylinder_count is not None:
        engine_spec.cylinder_count = request.cylinder_count
    if request.layout is not None:
        engine_spec.layout = request.layout
    if request.bore_mm is not None:
        engine_spec.bore_mm = request.bore_mm
    if request.stroke_mm is not None:
        engine_spec.stroke_mm = request.stroke_mm
    if request.compression_ratio is not None:
        engine_spec.compression_ratio = request.compression_ratio
    if request.rod_length_mm is not None:
        engine_spec.rod_length_mm = request.rod_length_mm
    if request.head_flow_stage is not None:
        engine_spec.valve_train.head_flow_stage = request.head_flow_stage
    if request.valves_per_cylinder is not None:
        engine_spec.valve_train.valves_per_cylinder = request.valves_per_cylinder
    if request.variable_valve_timing is not None:
        engine_spec.valve_train.variable_valve_timing = request.variable_valve_timing
    if request.cam_profile_id is not None:
        from app.services.catalog_seed import CAM_PROFILES  # local import to avoid circular misuse

        engine_spec.cam_profile = CAM_PROFILES[request.cam_profile_id]
    if request.intake_cam_duration_deg is not None:
        engine_spec.intake_cam_duration_deg = request.intake_cam_duration_deg
    if request.exhaust_cam_duration_deg is not None:
        engine_spec.exhaust_cam_duration_deg = request.exhaust_cam_duration_deg
    if request.intake_lift_mm is not None:
        engine_spec.intake_lift_mm = request.intake_lift_mm
    if request.exhaust_lift_mm is not None:
        engine_spec.exhaust_lift_mm = request.exhaust_lift_mm
    if request.lobe_separation_deg is not None:
        engine_spec.lobe_separation_deg = request.lobe_separation_deg
    if request.induction_type is not None:
        engine_spec.induction.type = request.induction_type
    if request.boost_psi is not None:
        engine_spec.induction.boost_psi = request.boost_psi
    if request.compressor_efficiency is not None:
        engine_spec.compressor_efficiency = request.compressor_efficiency
    if request.intercooler_effectiveness is not None:
        engine_spec.intercooler_effectiveness = request.intercooler_effectiveness
    if request.fuel_type is not None:
        engine_spec.fuel.fuel_type = request.fuel_type
    if request.injector_scale is not None:
        engine_spec.fuel.injector_scale = request.injector_scale
    if request.pump_scale is not None:
        engine_spec.fuel.pump_scale = request.pump_scale
    if request.target_lambda is not None:
        engine_spec.target_lambda = request.target_lambda
    if request.ignition_advance_bias_deg is not None:
        engine_spec.ignition_advance_bias_deg = request.ignition_advance_bias_deg
    if request.exhaust_style is not None:
        engine_spec.exhaust.exhaust_style = request.exhaust_style
    if request.exhaust_backpressure_factor is not None:
        engine_spec.exhaust_backpressure_factor = request.exhaust_backpressure_factor
    if request.tune_bias is not None:
        engine_spec.tune_bias = request.tune_bias
    if request.rev_limit_rpm is not None:
        engine_spec.rev_limit_rpm = request.rev_limit_rpm
    if request.radiator_effectiveness is not None:
        engine_spec.radiator_effectiveness = request.radiator_effectiveness
    if request.ambient_temp_c is not None:
        engine_spec.ambient_temp_c = request.ambient_temp_c
    if request.altitude_m is not None:
        engine_spec.altitude_m = request.altitude_m

    selections = []
    for selection in build.selections:
        if selection.subsystem == "engine":
            selections.append(_new_selection(subsystem="engine", config_id=engine_spec.config_id, source="manual"))
        else:
            selections.append(selection)

    updated = build.model_copy(
        update={
            "engine_build_spec": engine_spec,
            "selections": selections,
            "active_notes": [f"Engine builder updated: {engine_spec.label}."],
        }
    )
    updated = _normalize_build(updated)
    return get_build_store().save(updated)


def patch_drivetrain(build_id: str, request: PatchDrivetrainRequest) -> BuildState:
    build = get_build(build_id)
    drivetrain = build.drivetrain_config.model_copy(deep=True)

    if request.label is not None:
        drivetrain.label = request.label
    if request.transmission_mode is not None:
        drivetrain.transmission_mode = request.transmission_mode
    if request.gear_ratios is not None:
        drivetrain.gear_ratios = request.gear_ratios
    if request.final_drive_ratio is not None:
        drivetrain.final_drive_ratio = request.final_drive_ratio
    if request.driveline_loss_factor is not None:
        drivetrain.driveline_loss_factor = request.driveline_loss_factor
    if request.differential_bias is not None:
        drivetrain.differential_bias = request.differential_bias
    if request.shift_latency_ms is not None:
        drivetrain.shift_latency_ms = request.shift_latency_ms

    updated = build.model_copy(
        update={
            "drivetrain_config": drivetrain,
            "active_notes": [f"Drivetrain updated: {drivetrain.label}."],
        }
    )
    updated = _normalize_build(updated)
    return get_build_store().save(updated)


def clone_build(build_id: str) -> CloneBuildResponse:
    build = get_build(build_id)
    cloned = build.model_copy(update={"build_id": str(uuid4())}, deep=True)
    cloned = _normalize_build(cloned)
    get_build_store().save(cloned)
    return CloneBuildResponse(build_id=cloned.build_id, source_build_id=build_id)


def apply_preset(build_id: str, preset_id: str, repository: CatalogRepository | None = None) -> PresetApplicationResponse:
    repository = repository or get_repository()
    preset = repository.get_preset(preset_id)
    build = patch_build(
        build_id,
        PatchBuildPartsRequest(parts=preset.patch, scenario_name=preset.scenario_name),
        repository=repository,
    )
    return PresetApplicationResponse(build=build, applied_preset=preset)


def build_detail(build_id: str, repository: CatalogRepository | None = None) -> BuildDetailResponse:
    repository = repository or get_repository()
    build = get_build(build_id)
    return BuildDetailResponse(
        build=build,
        available_parts=repository.list_parts_for_trim(build.vehicle.trim_id),
        available_presets=repository.list_presets(),
        scenario_definitions=repository.list_scenarios(),
        engine_families=repository.list_engine_families(),
        import_batches=repository.list_import_batches(),
    )
