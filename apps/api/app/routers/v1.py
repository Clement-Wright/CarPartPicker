from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.production_schemas import (
    BuildAssemblyPatchRequest,
    BuildSceneResponse,
    BuildValidationReport,
    CatalogSourceContractsResponse,
    PartDetailV1,
    PartPricesResponse,
    PartSearchResponse,
    SimulationResponse,
    VehicleDetailV1,
    VehicleSearchResponse,
)
from app.schemas import BuildState, CreateBuildRequest, PatchBuildPartsRequest
from app.services.assembly_graph_service import build_scene_response, build_validation_report, simulate_build
from app.services.build_state_service import create_build, get_build, patch_build, patch_drivetrain, patch_engine
from app.services.production_mapper_service import (
    catalog_source_contracts,
    get_part_prices_v1,
    get_part_v1,
    get_vehicle_v1,
    list_parts_v1,
    list_vehicles_v1,
)

router = APIRouter(prefix="/v1", tags=["v1"])


@router.get("/vehicles/search", response_model=VehicleSearchResponse)
def vehicle_search_endpoint(
    q: str | None = None,
    transmission: str | None = Query(default=None, pattern="^(manual|automatic)$"),
) -> VehicleSearchResponse:
    return list_vehicles_v1(query=q, transmission=transmission)


@router.get("/vehicles/{vehicle_id}", response_model=VehicleDetailV1)
def vehicle_detail_endpoint(vehicle_id: str) -> VehicleDetailV1:
    return get_vehicle_v1(vehicle_id)


@router.get("/parts/search", response_model=PartSearchResponse)
def part_search_endpoint(
    q: str | None = None,
    subsystem: str | None = None,
    tag: str | None = None,
) -> PartSearchResponse:
    return list_parts_v1(query=q, subsystem=subsystem, tag=tag)


@router.get("/parts/{part_id}/prices", response_model=PartPricesResponse)
def part_prices_endpoint(part_id: str) -> PartPricesResponse:
    return get_part_prices_v1(part_id)


@router.get("/parts/{part_id}", response_model=PartDetailV1)
def part_detail_endpoint(part_id: str) -> PartDetailV1:
    return get_part_v1(part_id)


@router.get("/catalog/contracts", response_model=CatalogSourceContractsResponse)
def catalog_contracts_endpoint() -> CatalogSourceContractsResponse:
    return catalog_source_contracts()


@router.post("/builds", response_model=BuildState)
def create_build_v1_endpoint(request: CreateBuildRequest) -> BuildState:
    return create_build(request)


@router.get("/builds/{build_id}", response_model=BuildState)
def get_build_v1_endpoint(build_id: str) -> BuildState:
    return get_build(build_id)


@router.patch("/builds/{build_id}/assembly", response_model=BuildState)
def patch_build_assembly_endpoint(build_id: str, request: BuildAssemblyPatchRequest) -> BuildState:
    build = get_build(build_id)

    if request.parts or request.scenario_name or request.target_metrics is not None or request.tolerances is not None:
        build = patch_build(
            build_id,
            PatchBuildPartsRequest(
                parts=request.parts,
                scenario_name=request.scenario_name,
                target_metrics=request.target_metrics,
                tolerances=request.tolerances,
            ),
        )

    if request.engine_patch is not None:
        build = patch_engine(build_id, request.engine_patch)

    if request.drivetrain_patch is not None:
        build = patch_drivetrain(build_id, request.drivetrain_patch)

    return build


@router.post("/builds/{build_id}/validate", response_model=BuildValidationReport)
def validate_build_v1_endpoint(build_id: str) -> BuildValidationReport:
    return build_validation_report(get_build(build_id))


@router.get("/builds/{build_id}/scene", response_model=BuildSceneResponse)
def scene_build_v1_endpoint(build_id: str) -> BuildSceneResponse:
    return build_scene_response(get_build(build_id))


@router.post("/builds/{build_id}/simulate/{mode}", response_model=SimulationResponse)
def simulate_build_v1_endpoint(build_id: str, mode: str) -> SimulationResponse:
    if mode not in {"engine", "vehicle", "thermal", "braking", "handling"}:
        raise HTTPException(status_code=404, detail="Unknown simulation mode.")
    return simulate_build(get_build(build_id), mode)
