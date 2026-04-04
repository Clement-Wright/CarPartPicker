from __future__ import annotations

from app.schemas import BuildState, ValidationFinding
from app.services.build_helpers import active_engine_family, selected_parts
from app.services.catalog_seed import prov


def run_interface_checks(build: BuildState) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    parts = selected_parts(build)
    engine_family = active_engine_family(build)
    transmission = parts["transmission"]

    for subsystem, part in parts.items():
        if build.vehicle.platform not in part.compatible_platforms:
            findings.append(
                ValidationFinding(
                    finding_id=f"interface-{subsystem}-platform",
                    phase="fast",
                    category="interface",
                    severity="BLOCKER",
                    subsystem=subsystem,
                    title="Platform mismatch",
                    detail=f"{part.label} is not scoped for the {build.vehicle.platform.upper()} platform.",
                    blocking=True,
                    related_parts=[part.part_id],
                    provenance=prov("interface_validation_service", "platform compatibility rule"),
                )
            )

        if build.vehicle.transmission not in part.compatible_transmissions and "any" not in part.compatible_transmissions:
            findings.append(
                ValidationFinding(
                    finding_id=f"interface-{subsystem}-transmission",
                    phase="fast",
                    category="interface",
                    severity="BLOCKER",
                    subsystem=subsystem,
                    title="Transmission mismatch",
                    detail=f"{part.label} does not match the {build.vehicle.transmission} driveline configuration.",
                    blocking=True,
                    related_parts=[part.part_id],
                    provenance=prov("interface_validation_service", "transmission compatibility rule"),
                )
            )

    if build.drivetrain_config.transmission_mode != build.vehicle.transmission:
        findings.append(
            ValidationFinding(
                finding_id="interface-drivetrain-mode",
                phase="fast",
                category="interface",
                severity="WARNING",
                subsystem="transmission",
                title="Drivetrain config and selected trim mode differ",
                detail=f"The active drivetrain config is {build.drivetrain_config.transmission_mode}, while the base trim is {build.vehicle.transmission}.",
                related_parts=[transmission.part_id],
                provenance=prov("interface_validation_service", "drivetrain config consistency rule"),
            )
        )

    if engine_family.mount_interface.mount_family != build.vehicle_platform.stock_mount_family:
        findings.append(
            ValidationFinding(
                finding_id="interface-engine-mount",
                phase="fast",
                category="interface",
                severity="FABRICATION_REQUIRED" if build.tolerances.allow_fabrication else "BLOCKER",
                subsystem="engine",
                title="Engine mount family mismatch",
                detail=f"{engine_family.label} uses {engine_family.mount_interface.mount_family}, but the chassis expects {build.vehicle_platform.stock_mount_family}.",
                blocking=not build.tolerances.allow_fabrication,
                related_configs=[build.engine_build_spec.config_id],
                provenance=prov("interface_validation_service", "mount family compatibility rule"),
            )
        )

    if transmission.interface.bellhousing_family and transmission.interface.bellhousing_family != engine_family.bellhousing_interface.bellhousing_family:
        findings.append(
            ValidationFinding(
                finding_id="interface-bellhousing",
                phase="fast",
                category="interface",
                severity="BLOCKER",
                subsystem="transmission",
                title="Bellhousing interface mismatch",
                detail=f"{engine_family.label} expects {engine_family.bellhousing_interface.bellhousing_family}, but {transmission.label} exposes {transmission.interface.bellhousing_family}.",
                blocking=True,
                related_parts=[transmission.part_id],
                related_configs=[build.engine_build_spec.config_id],
                provenance=prov("interface_validation_service", "bellhousing family compatibility rule"),
            )
        )

    if engine_family.electrical_interface.ecu_family != build.vehicle_platform.stock_ecu_family and parts["tune"].part_id == "tune_stock":
        findings.append(
            ValidationFinding(
                finding_id="interface-ecu-family",
                phase="fast",
                category="interface",
                severity="WARNING",
                subsystem="tune",
                title="Standalone ECU path implied",
                detail=f"{engine_family.label} uses {engine_family.electrical_interface.ecu_family}, so the stock ECU path is only partially compatible.",
                related_parts=[parts["tune"].part_id],
                related_configs=[build.engine_build_spec.config_id],
                provenance=prov("interface_validation_service", "electrical family compatibility rule"),
            )
        )

    return findings
