from __future__ import annotations

from app.schemas import BuildState, ValidationFinding
from app.services.build_helpers import active_engine_family, selected_parts
from app.services.catalog_seed import prov


def run_geometry_checks(build: BuildState, *, phase: str = "fast") -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    parts = selected_parts(build)
    wheels = parts["wheels"]
    brakes = parts["brakes"]
    tires = parts["tires"]
    suspension = parts["suspension"]
    body = parts["body_aero"]
    forced_induction = parts["forced_induction"]
    engine_family = active_engine_family(build)

    wheel_diameter = wheels.geometry.wheel_diameter_in or build.vehicle.stock_wheel_diameter
    minimum_brake_wheel = brakes.geometry.brake_min_wheel_in or 0
    if wheel_diameter < minimum_brake_wheel:
        findings.append(
            ValidationFinding(
                finding_id="geometry-wheel-brake-clearance",
                phase=phase,
                category="geometry",
                severity="BLOCKER",
                subsystem="wheels",
                title="Wheel-to-brake clearance failure",
                detail=f"{wheels.label} is {wheel_diameter:.0f}-inch, but {brakes.label} needs at least {minimum_brake_wheel:.0f}-inch clearance.",
                blocking=True,
                related_parts=[wheels.part_id, brakes.part_id],
                provenance=prov("geometry_validation_service", "wheel barrel vs brake envelope rule"),
            )
        )

    hood_need = max(forced_induction.geometry.hood_clearance_needed_mm, max(0.0, engine_family.envelope.height_mm - build.chassis_envelope.engine_bay.height_mm))
    hood_gain = body.geometry.hood_clearance_gain_mm
    if hood_need > hood_gain:
        findings.append(
            ValidationFinding(
                finding_id="geometry-hood-clearance",
                phase=phase,
                category="geometry",
                severity="WARNING" if phase == "fast" else "BLOCKER",
                subsystem="body_aero",
                title="Hood clearance margin is insufficient",
                detail=f"The active engine/induction package needs {hood_need:.0f} mm of extra vertical clearance, but the selected body state only adds {hood_gain:.0f} mm.",
                blocking=phase == "heavy",
                related_parts=[forced_induction.part_id, body.part_id],
                related_configs=[build.engine_build_spec.config_id],
                provenance=prov("geometry_validation_service", "hood envelope approximation"),
            )
        )

    if engine_family.envelope.length_mm > build.chassis_envelope.engine_bay.length_mm or engine_family.envelope.width_mm > build.chassis_envelope.engine_bay.width_mm:
        findings.append(
            ValidationFinding(
                finding_id="geometry-engine-bay",
                phase=phase,
                category="geometry",
                severity="BLOCKER" if phase == "heavy" else "WARNING",
                subsystem="engine",
                title="Engine bay packaging is over envelope",
                detail=f"{engine_family.label} exceeds the seeded engine bay envelope for the {build.vehicle.platform.upper()} chassis.",
                blocking=phase == "heavy",
                related_configs=[build.engine_build_spec.config_id],
                provenance=prov("geometry_validation_service", "engine bay bounding-envelope rule"),
            )
        )

    rub_risk = (tires.geometry.tire_rub_risk or 0) + (suspension.geometry.tire_rub_risk or 0)
    if rub_risk >= 0.28:
        findings.append(
            ValidationFinding(
                finding_id="geometry-tire-rub",
                phase=phase,
                category="geometry",
                severity="WARNING" if phase == "fast" else "SCENARIO_PENALTY",
                subsystem="tires",
                title="Tire rub risk rises under compression",
                detail="The current tire width and ride-height combination risks rubbing at lock and compression.",
                related_parts=[tires.part_id, suspension.part_id],
                provenance=prov("geometry_validation_service", "tire sweep envelope approximation"),
            )
        )

    return findings
