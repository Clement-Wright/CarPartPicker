from __future__ import annotations

from datetime import datetime, timezone

from app.schemas import BuildState, RenderConfig, RenderHighlight, RenderSceneObject
from app.services.build_helpers import active_engine_family, selected_parts
from app.services.validation_service import build_validation_snapshot


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_render_config(build: BuildState) -> RenderConfig:
    parts = selected_parts(build)
    validation = build_validation_snapshot(build, phase="fast")
    ride_drop = parts["suspension"].geometry.ride_height_drop_mm
    engine_family = active_engine_family(build)
    highlights: list[RenderHighlight] = []
    objects: list[RenderSceneObject] = []

    severity_by_part: dict[str, str] = {}
    severity_by_config: dict[str, str] = {}
    for finding in validation.findings:
        for part_id in finding.related_parts:
            severity_by_part[part_id] = "error" if finding.severity == "BLOCKER" else "warning"
        for config_id in finding.related_configs:
            severity_by_config[config_id] = "error" if finding.severity == "BLOCKER" else "warning"
        if finding.category == "geometry" or finding.severity == "FABRICATION_REQUIRED":
            highlights.append(
                RenderHighlight(
                    zone=finding.subsystem,
                    severity="error" if finding.severity == "BLOCKER" else "warning",
                    message=finding.detail,
                )
            )

    for subsystem, part in parts.items():
        asset = part.visual
        if subsystem == "wheels":
            for corner, x, z in [
                ("front_left", -0.82, 1.05),
                ("front_right", 0.82, 1.05),
                ("rear_left", -0.82, -1.05),
                ("rear_right", 0.82, -1.05),
            ]:
                objects.append(
                    RenderSceneObject(
                        object_id=f"{part.part_id}-{corner}",
                        slot=corner,
                        kind=asset.kind,
                        color=asset.color,
                        position=(x, -0.3 - (ride_drop / 200), z),
                        scale=asset.scale,
                        rotation=asset.rotation,
                        highlight=severity_by_part.get(part.part_id, "none"),
                    )
                )
            continue
        if subsystem == "brakes":
            for corner, x, z in [
                ("front_left_brake", -0.72, 1.05),
                ("front_right_brake", 0.72, 1.05),
                ("rear_left_brake", -0.72, -1.05),
                ("rear_right_brake", 0.72, -1.05),
            ]:
                objects.append(
                    RenderSceneObject(
                        object_id=f"{part.part_id}-{corner}",
                        slot=corner,
                        kind=asset.kind,
                        color=asset.color,
                        position=(x, -0.28 - (ride_drop / 220), z),
                        scale=asset.scale,
                        rotation=asset.rotation,
                        highlight=severity_by_part.get(part.part_id, "none"),
                    )
                )
            continue
        if subsystem == "tires":
            continue
        objects.append(
            RenderSceneObject(
                object_id=part.part_id,
                slot=asset.slot,
                kind=asset.kind,
                color=asset.color,
                position=(asset.position[0], asset.position[1] - (ride_drop / 250), asset.position[2]),
                scale=asset.scale,
                rotation=asset.rotation,
                visible=asset.visible,
                highlight=severity_by_part.get(part.part_id, "none"),
            )
        )

    engine_kind = "swap_v6" if "v6" in engine_family.tags or build.engine_build_spec.layout == "v6" else "swap_turbo" if "turbo" in engine_family.tags else "flat4"
    objects.append(
        RenderSceneObject(
            object_id=build.engine_build_spec.config_id,
            slot="engine_bay",
            kind=engine_kind,
            color="#7e8c97" if engine_family.engine_family_id == "fa24d_native" else "#ff7b31",
            position=(0.0, 0.18, 0.08 - (ride_drop / 700)),
            scale=(0.72, 0.48, 1.0) if build.engine_build_spec.layout == "v6" else (0.64, 0.42, 0.92),
            highlight=severity_by_config.get(build.engine_build_spec.config_id, "none"),
        )
    )
    if build.engine_build_spec.induction.intercooler_required:
        objects.append(
            RenderSceneObject(
                object_id=f"{build.engine_build_spec.config_id}-intercooler",
                slot="intercooler",
                kind="intercooler",
                color="#7ce7c6",
                position=(0.0, 0.02, 0.92),
                scale=(0.7, 0.18, 0.08),
                highlight=severity_by_config.get(build.engine_build_spec.config_id, "none"),
            )
        )

    if build.engine_build_spec.engine_family_id != "fa24d_native":
        highlights.append(
            RenderHighlight(
                zone="engine",
                severity="warning",
                message=f"{engine_family.label} is running through swap-mode validation with packaging and fabrication overlays enabled.",
            )
        )

    return RenderConfig(
        build_id=build.build_id,
        build_hash=build.computation.build_hash,
        ride_height_drop_mm=ride_drop,
        paint_color="#d7dde3",
        scene_objects=objects,
        highlights=highlights,
        computed_at=_now(),
    )
