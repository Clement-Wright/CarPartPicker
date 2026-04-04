from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas import (
    BuildDetailResponse,
    BuildDiffResponse,
    BuildDynoSnapshot,
    BuildMetricSnapshot,
    BuildScenarioSnapshot,
    BuildValidationSnapshot,
    CloneBuildResponse,
    CreateBuildRequest,
    GraphResponse,
    PatchBuildPartsRequest,
    PatchDrivetrainRequest,
    PatchEngineRequest,
    PresetApplicationResponse,
    RenderConfig,
    VehicleMetricSnapshot,
)
from app.services.build_state_service import (
    apply_preset,
    build_detail,
    clone_build,
    create_build,
    get_build,
    patch_build,
    patch_drivetrain,
    patch_engine,
)
from app.services.diff_service import build_diff
from app.services.dyno_service import build_dyno_snapshot
from app.services.graph_reasoning_service import build_graph_reasoning
from app.services.metrics_service import build_metric_snapshot
from app.services.render_config_service import build_render_config
from app.services.scenario_service import build_scenario_snapshot
from app.services.validation_service import build_validation_snapshot
from app.services.vehicle_metrics_service import build_vehicle_metric_snapshot

router = APIRouter(prefix="/builds", tags=["builds"])


@router.post("", response_model=BuildDetailResponse)
def create_build_endpoint(request: CreateBuildRequest) -> BuildDetailResponse:
    build = create_build(request)
    return build_detail(build.build_id)


@router.get("/{build_id}", response_model=BuildDetailResponse)
def get_build_endpoint(build_id: str) -> BuildDetailResponse:
    return build_detail(build_id)


@router.patch("/{build_id}/parts", response_model=BuildDetailResponse)
def patch_build_endpoint(build_id: str, request: PatchBuildPartsRequest) -> BuildDetailResponse:
    patch_build(build_id, request)
    return build_detail(build_id)


@router.patch("/{build_id}/engine", response_model=BuildDetailResponse)
def patch_engine_endpoint(build_id: str, request: PatchEngineRequest) -> BuildDetailResponse:
    patch_engine(build_id, request)
    return build_detail(build_id)


@router.patch("/{build_id}/drivetrain", response_model=BuildDetailResponse)
def patch_drivetrain_endpoint(build_id: str, request: PatchDrivetrainRequest) -> BuildDetailResponse:
    patch_drivetrain(build_id, request)
    return build_detail(build_id)


@router.post("/{build_id}/presets/{preset_id}/apply", response_model=PresetApplicationResponse)
def apply_preset_endpoint(build_id: str, preset_id: str) -> PresetApplicationResponse:
    return apply_preset(build_id, preset_id)


@router.get("/{build_id}/validate", response_model=BuildValidationSnapshot)
def validate_build_endpoint(build_id: str, phase: str = Query(default="fast", pattern="^(fast|heavy)$")) -> BuildValidationSnapshot:
    return build_validation_snapshot(get_build(build_id), phase=phase)


@router.get("/{build_id}/metrics", response_model=BuildMetricSnapshot)
def metrics_endpoint(build_id: str) -> BuildMetricSnapshot:
    return build_metric_snapshot(get_build(build_id))


@router.get("/{build_id}/vehicle-metrics", response_model=VehicleMetricSnapshot)
def vehicle_metrics_endpoint(build_id: str) -> VehicleMetricSnapshot:
    return build_vehicle_metric_snapshot(get_build(build_id))


@router.get("/{build_id}/dyno", response_model=BuildDynoSnapshot)
def dyno_endpoint(build_id: str) -> BuildDynoSnapshot:
    return build_dyno_snapshot(get_build(build_id))


@router.get("/{build_id}/scenario", response_model=BuildScenarioSnapshot)
def scenario_endpoint(build_id: str, name: str | None = None) -> BuildScenarioSnapshot:
    return build_scenario_snapshot(get_build(build_id), scenario_name=name)


@router.get("/{build_id}/render-config", response_model=RenderConfig)
def render_config_endpoint(build_id: str) -> RenderConfig:
    return build_render_config(get_build(build_id))


@router.get("/{build_id}/graph", response_model=GraphResponse)
def graph_endpoint(build_id: str) -> GraphResponse:
    return build_graph_reasoning(build_id)


@router.get("/{build_id}/diff", response_model=BuildDiffResponse)
def diff_endpoint(build_id: str, against: str = "stock") -> BuildDiffResponse:
    return build_diff(build_id, against)


@router.post("/{build_id}/clone", response_model=CloneBuildResponse)
def clone_endpoint(build_id: str) -> CloneBuildResponse:
    return clone_build(build_id)
