from __future__ import annotations

from collections import defaultdict

from app.production_schemas import CompatibilityDiagnostic, CompatibilityStageSummary
from app.schemas import BuildState
from app.services.build_helpers import active_engine_family, selected_parts
from app.services.engine_simulation_service import build_engine_simulation_snapshot
from app.services.seed_repository import CatalogRepository, get_repository


def _severity(level: str) -> str:
    if level == "BLOCKER":
        return "error"
    if level == "FABRICATION_REQUIRED":
        return "fabrication"
    return "warning"


def _provenance_dict(value) -> dict[str, object]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return dict(value)


def build_compatibility_diagnostics(
    build: BuildState,
    *,
    repository: CatalogRepository | None = None,
) -> tuple[list[CompatibilityDiagnostic], list[CompatibilityStageSummary]]:
    repository = repository or get_repository()
    diagnostics: list[CompatibilityDiagnostic] = []
    parts = selected_parts(build, repository=repository)
    engine_family = active_engine_family(build, repository=repository)
    dyno = build_engine_simulation_snapshot(build).dyno

    def add(
        *,
        stage: str,
        error_code: str,
        severity: str,
        subsystem: str,
        source_part_or_config: str,
        target_part_or_slot: str,
        explanation: str,
        suggested_fix: str,
        provenance,
    ) -> None:
        diagnostics.append(
            CompatibilityDiagnostic(
                stage=stage,
                error_code=error_code,
                severity=severity,
                source_part_or_config=source_part_or_config,
                target_part_or_slot=target_part_or_slot,
                subsystem=subsystem,
                explanation=explanation,
                suggested_fix=suggested_fix,
                provenance=_provenance_dict(provenance),
            )
        )

    for subsystem, part in parts.items():
        record = repository.get_part_record(part.part_id) if hasattr(repository, "get_part_record") else None
        if record is None:
            continue
        application = next((item for item in record.applications if item.vehicle_id == build.vehicle.trim_id), None)
        if application is None:
            add(
                stage="keyed_compatibility",
                error_code="VEHICLE_APPLICATION_MISMATCH",
                severity="error",
                subsystem=subsystem,
                source_part_or_config=part.part_id,
                target_part_or_slot=build.vehicle.trim_id,
                explanation=f"{part.label} has no imported application coverage for {build.vehicle.trim_id}.",
                suggested_fix="Choose a part with direct application coverage for this vehicle.",
                provenance=record.provenance,
            )
            continue
        if application.fitment_status == "fits_with_adapter":
            add(
                stage="keyed_compatibility",
                error_code="APPLICATION_REQUIRES_ADAPTER",
                severity="warning",
                subsystem=subsystem,
                source_part_or_config=part.part_id,
                target_part_or_slot=build.vehicle.trim_id,
                explanation="This part is only supported through an adapter path for the selected vehicle.",
                suggested_fix="Add the required adapter hardware or choose a direct-fit alternative.",
                provenance=application.provenance,
            )
        if application.fitment_status == "fits_with_fabrication":
            add(
                stage="keyed_compatibility",
                error_code="APPLICATION_REQUIRES_FABRICATION",
                severity="fabrication",
                subsystem=subsystem,
                source_part_or_config=part.part_id,
                target_part_or_slot=build.vehicle.trim_id,
                explanation="This part is only supported through fabrication work for the selected vehicle.",
                suggested_fix="Enable fabrication tolerance or choose a direct-fit alternative.",
                provenance=application.provenance,
            )

    wheels = parts.get("wheels")
    tires = parts.get("tires")
    brakes = parts.get("brakes")
    transmission = parts.get("transmission")
    tune = parts.get("tune")
    cooling = parts.get("cooling")

    if wheels is not None:
        if wheels.interface.wheel_bolt_pattern != build.vehicle_platform.wheel_bolt_pattern:
            add(
                stage="keyed_compatibility",
                error_code="WHEEL_BOLT_PATTERN_MISMATCH",
                severity="error",
                subsystem="wheels",
                source_part_or_config=wheels.part_id,
                target_part_or_slot="front_left_hub",
                explanation=f"{wheels.label} uses {wheels.interface.wheel_bolt_pattern}, but the chassis expects {build.vehicle_platform.wheel_bolt_pattern}.",
                suggested_fix="Choose a wheel with the correct bolt pattern or add a compatible adapter.",
                provenance=wheels.provenance,
            )
        if wheels.interface.hub_bore_mm and abs(wheels.interface.hub_bore_mm - build.vehicle_platform.hub_bore_mm) > 0.01:
            add(
                stage="keyed_compatibility",
                error_code="WHEEL_HUB_BORE_MISMATCH",
                severity="warning",
                subsystem="wheels",
                source_part_or_config=wheels.part_id,
                target_part_or_slot="front_left_hub",
                explanation=f"{wheels.label} hub bore is {wheels.interface.hub_bore_mm:.1f} mm, while the chassis hub bore is {build.vehicle_platform.hub_bore_mm:.1f} mm.",
                suggested_fix="Use a hub-centric ring or choose a wheel with the correct hub bore.",
                provenance=wheels.provenance,
            )

    if engine_family.mount_interface.mount_family != build.vehicle_platform.stock_mount_family:
        add(
            stage="keyed_compatibility",
            error_code="ENGINE_MOUNT_FAMILY_MISMATCH",
            severity="fabrication" if build.tolerances.allow_fabrication else "error",
            subsystem="engine",
            source_part_or_config=build.engine_build_spec.config_id,
            target_part_or_slot="engine_bay",
            explanation=f"{engine_family.label} uses {engine_family.mount_interface.mount_family}, but the chassis expects {build.vehicle_platform.stock_mount_family}.",
            suggested_fix="Choose an engine family with the stock mount family or add a swap-mount solution.",
            provenance=engine_family.provenance,
        )

    if transmission is not None and transmission.interface.bellhousing_family != engine_family.bellhousing_interface.bellhousing_family:
        add(
            stage="keyed_compatibility",
            error_code="BELLHOUSING_PATTERN_MISMATCH",
            severity="error",
            subsystem="transmission",
            source_part_or_config=transmission.part_id,
            target_part_or_slot=build.engine_build_spec.config_id,
            explanation=f"{transmission.label} exposes {transmission.interface.bellhousing_family}, but the engine expects {engine_family.bellhousing_interface.bellhousing_family}.",
            suggested_fix="Choose a transmission with the matching bellhousing pattern or add the correct adapter bellhousing.",
            provenance=transmission.provenance,
        )

    if wheels is not None and tires is not None:
        tire_width = tires.geometry.tire_width_mm or 0.0
        min_width = wheels.capabilities.get("min_tire_width_mm")
        max_width = wheels.capabilities.get("max_tire_width_mm")
        if min_width and tire_width < min_width:
            add(
                stage="keyed_compatibility",
                error_code="TIRE_TOO_NARROW_FOR_WHEEL",
                severity="warning",
                subsystem="tires",
                source_part_or_config=tires.part_id,
                target_part_or_slot=wheels.part_id,
                explanation=f"{tires.label} is {tire_width:.0f} mm wide, below the wheel's minimum supported width of {min_width:.0f} mm.",
                suggested_fix="Choose a wider tire or a narrower wheel.",
                provenance=tires.provenance,
            )
        if max_width and tire_width > max_width:
            add(
                stage="keyed_compatibility",
                error_code="TIRE_TOO_WIDE_FOR_WHEEL",
                severity="error",
                subsystem="tires",
                source_part_or_config=tires.part_id,
                target_part_or_slot=wheels.part_id,
                explanation=f"{tires.label} is {tire_width:.0f} mm wide, above the wheel's supported width of {max_width:.0f} mm.",
                suggested_fix="Choose a narrower tire or a wider wheel.",
                provenance=tires.provenance,
            )

    if engine_family.envelope.length_mm > build.chassis_envelope.engine_bay.length_mm or engine_family.envelope.width_mm > build.chassis_envelope.engine_bay.width_mm:
        add(
            stage="dimensional_compatibility",
            error_code="ENGINE_BAY_ENVELOPE_EXCEEDED",
            severity="error",
            subsystem="engine",
            source_part_or_config=build.engine_build_spec.config_id,
            target_part_or_slot="engine_bay",
            explanation=f"{engine_family.label} exceeds the current engine bay envelope for the {build.vehicle.platform.upper()} chassis.",
            suggested_fix="Choose a smaller engine package or rework the bay and crossmember for the swap.",
            provenance=engine_family.provenance,
        )

    if wheels is not None and brakes is not None:
        wheel_diameter = wheels.geometry.wheel_diameter_in or build.vehicle.stock_wheel_diameter
        brake_requirement = brakes.geometry.brake_min_wheel_in or 0.0
        if wheel_diameter < brake_requirement:
            add(
                stage="dimensional_compatibility",
                error_code="BRAKE_WHEEL_CLEARANCE_FAILURE",
                severity="error",
                subsystem="brakes",
                source_part_or_config=brakes.part_id,
                target_part_or_slot=wheels.part_id,
                explanation=f"{brakes.label} needs at least an {brake_requirement:.0f}-inch wheel, but {wheels.label} is {wheel_diameter:.0f}-inch.",
                suggested_fix="Choose a larger wheel or a brake package with a smaller clearance requirement.",
                provenance=brakes.provenance,
            )

    suspension = parts.get("suspension")
    if tires is not None:
        tire_width = tires.geometry.tire_width_mm or 0.0
        if tire_width > build.chassis_envelope.front_tire_sweep.nominal_width_mm:
            add(
                stage="dimensional_compatibility",
                error_code="TIRE_SWEEP_MARGIN_EXCEEDED",
                severity="warning",
                subsystem="tires",
                source_part_or_config=tires.part_id,
                target_part_or_slot="front_left_hub",
                explanation=f"{tires.label} exceeds the nominal front tire sweep width of {build.chassis_envelope.front_tire_sweep.nominal_width_mm:.0f} mm.",
                suggested_fix="Choose a narrower tire or increase clearance through suspension and alignment changes.",
                provenance=tires.provenance,
            )
        rub_risk = (tires.geometry.tire_rub_risk or 0.0) + (
            (suspension.geometry.tire_rub_risk or 0.0) if suspension is not None else 0.0
        )
        if rub_risk >= 0.28:
            add(
                stage="dimensional_compatibility",
                error_code="TIRE_RUB_MARGIN_LOW",
                severity="warning",
                subsystem="tires",
                source_part_or_config=tires.part_id,
                target_part_or_slot="front_left_hub",
                explanation="The current tire width and suspension package have a high rub risk under lock and compression.",
                suggested_fix="Reduce tire width, add clearance, or raise ride height.",
                provenance=tires.provenance,
            )

    if transmission is not None and transmission.interface.drivetrain_family and transmission.interface.drivetrain_family != engine_family.driveline_interface.drivetrain_family:
        add(
            stage="systems_compatibility",
            error_code="DRIVELINE_FAMILY_MISMATCH",
            severity="warning",
            subsystem="transmission",
            source_part_or_config=transmission.part_id,
            target_part_or_slot=build.engine_build_spec.config_id,
            explanation=f"{transmission.label} targets {transmission.interface.drivetrain_family}, while the engine package expects {engine_family.driveline_interface.drivetrain_family}.",
            suggested_fix="Choose a transmission matched to the engine driveline family or add the correct adapter driveline package.",
            provenance=transmission.provenance,
        )

    if build.vehicle.driveline_limit_lbft < dyno.peak_torque_lbft:
        add(
            stage="systems_compatibility",
            error_code="VEHICLE_DRIVELINE_LIMIT_EXCEEDED",
            severity="warning",
            subsystem="transmission",
            source_part_or_config=build.engine_build_spec.config_id,
            target_part_or_slot="vehicle_driveline_limit",
            explanation=f"Estimated torque is {dyno.peak_torque_lbft:.0f} lb-ft, above the vehicle baseline limit of {build.vehicle.driveline_limit_lbft:.0f} lb-ft.",
            suggested_fix="Upgrade the driveline path or reduce torque output.",
            provenance=engine_family.provenance,
        )

    for subsystem_name in ("transmission", "clutch", "differential"):
        part = parts.get(subsystem_name)
        if part is None:
            continue
        capacity = part.capabilities.get("torque_capacity")
        if capacity and dyno.peak_torque_lbft > capacity:
            add(
                stage="systems_compatibility",
                error_code="TORQUE_CAPACITY_EXCEEDED",
                severity="error" if subsystem_name != "differential" else "warning",
                subsystem=subsystem_name,
                source_part_or_config=build.engine_build_spec.config_id,
                target_part_or_slot=part.part_id,
                explanation=f"Estimated torque is {dyno.peak_torque_lbft:.0f} lb-ft, above {part.label}'s rated capacity of {capacity:.0f} lb-ft.",
                suggested_fix="Choose a higher-capacity driveline component or reduce torque output.",
                provenance=part.provenance,
            )

    if tune is not None and engine_family.electrical_interface.ecu_family != build.vehicle_platform.stock_ecu_family and tune.part_id == "tune_stock":
        add(
            stage="systems_compatibility",
            error_code="ECU_PATH_INCOMPATIBLE",
            severity="warning",
            subsystem="tune",
            source_part_or_config=tune.part_id,
            target_part_or_slot=build.engine_build_spec.config_id,
            explanation="The selected engine package requires a different ECU family than the stock tune path provides.",
            suggested_fix="Choose a standalone or compatible tune package for the swap ECU family.",
            provenance=tune.provenance,
        )

    if cooling is not None and engine_family.cooling_interface.cooling_family != build.vehicle_platform.stock_cooling_family and cooling.part_id == "cooling_stock":
        add(
            stage="systems_compatibility",
            error_code="COOLING_PATH_INSUFFICIENT",
            severity="warning",
            subsystem="cooling",
            source_part_or_config=cooling.part_id,
            target_part_or_slot=build.engine_build_spec.config_id,
            explanation="The selected engine package expects a different cooling family than the stock cooling path provides.",
            suggested_fix="Choose a higher-capacity cooling package matched to the engine's cooling family.",
            provenance=cooling.provenance,
        )

    selected_ids = {part.part_id for part in parts.values()}
    for required_part_id in engine_family.required_supporting_part_ids:
        if required_part_id not in selected_ids:
            add(
                stage="dependency_rules",
                error_code="REQUIRED_SUPPORTING_PART_MISSING",
                severity="error",
                subsystem="engine",
                source_part_or_config=build.engine_build_spec.config_id,
                target_part_or_slot=required_part_id,
                explanation=f"{engine_family.label} requires {required_part_id.replace('_', ' ')} support before the build is physically supportable.",
                suggested_fix="Add the missing supporting part or switch to a less demanding engine package.",
                provenance=engine_family.provenance,
            )

    for fabrication in engine_family.fabrication_requirements:
        add(
            stage="dependency_rules",
            error_code="FABRICATION_STEP_REQUIRED",
            severity="fabrication" if build.tolerances.allow_fabrication else "error",
            subsystem="engine",
            source_part_or_config=build.engine_build_spec.config_id,
            target_part_or_slot=fabrication.fabrication_id,
            explanation=fabrication.detail,
            suggested_fix="Enable fabrication tolerance or choose a package that does not require custom fabrication.",
            provenance=engine_family.provenance,
        )

    stage_buckets: dict[str, list[CompatibilityDiagnostic]] = defaultdict(list)
    for diagnostic in diagnostics:
        stage_buckets[diagnostic.stage].append(diagnostic)

    stage_order = [
        "keyed_compatibility",
        "dimensional_compatibility",
        "systems_compatibility",
        "dependency_rules",
    ]
    summaries = [
        CompatibilityStageSummary(
            stage=stage,
            diagnostics=len(stage_buckets[stage]),
            errors=sum(1 for item in stage_buckets[stage] if item.severity == "error"),
            warnings=sum(1 for item in stage_buckets[stage] if item.severity == "warning"),
            fabrication=sum(1 for item in stage_buckets[stage] if item.severity == "fabrication"),
        )
        for stage in stage_order
    ]
    return diagnostics, summaries
