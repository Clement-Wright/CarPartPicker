from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from app.schemas import (
    BuildState,
    BuildValidationSnapshot,
    PatchDrivetrainRequest,
    PatchEngineRequest,
    QueryTolerance,
    RenderConfig,
    StrictModel,
    TargetMetrics,
    VehicleTrim,
)


CatalogDataMode = Literal["seed", "licensed", "verified"]
AssetReadinessStatus = Literal["approved_exact", "seed_proxy_only", "missing_exact_asset", "qa_blocked"]
FitmentStatus = Literal["direct_fit", "fits_with_adapter", "fits_with_fabrication", "simulation_only", "invalid"]
SimulationMode = Literal["engine", "vehicle", "thermal", "braking", "handling"]


class ReadinessNote(StrictModel):
    code: str
    message: str


class AssetReadiness(StrictModel):
    status: AssetReadinessStatus
    exact_mesh_approved: bool = False
    materials_approved: bool = False
    anchors_complete: bool = False
    collision_proxy_complete: bool = False
    qa_complete: bool = False
    notes: list[ReadinessNote] = Field(default_factory=list)


class PriceSnapshotView(StrictModel):
    source: str
    source_mode: CatalogDataMode
    price_usd: float
    currency: str = "USD"
    availability: str = "unknown"
    product_url: str | None = None
    observed_at: str


class PartSummaryV1(StrictModel):
    part_id: str
    subsystem: str
    label: str
    brand: str
    notes: str
    tags: list[str] = Field(default_factory=list)
    cost_usd: int
    source_mode: CatalogDataMode = "seed"
    production_ready: bool = False
    asset_readiness: AssetReadiness


class PartDetailV1(PartSummaryV1):
    compatible_platforms: list[str] = Field(default_factory=list)
    compatible_transmissions: list[str] = Field(default_factory=list)
    interface: dict[str, Any] = Field(default_factory=dict)
    geometry: dict[str, Any] = Field(default_factory=dict)
    performance: dict[str, Any] = Field(default_factory=dict)
    capabilities: dict[str, float] = Field(default_factory=dict)
    dependency_rules: list[dict[str, Any]] = Field(default_factory=list)
    visual: dict[str, Any] = Field(default_factory=dict)


class PartSearchResponse(StrictModel):
    items: list[PartSummaryV1]
    total: int
    source_mode: CatalogDataMode = "seed"


class PartPricesResponse(StrictModel):
    part_id: str
    snapshots: list[PriceSnapshotView]


class VehicleSearchItem(StrictModel):
    trim_id: str
    label: str
    platform: str
    transmission: str
    body_style: str
    source_mode: CatalogDataMode = "seed"
    supported_domains: list[str] = Field(default_factory=lambda: ["ice_road_vehicle"])


class VehicleSearchResponse(StrictModel):
    items: list[VehicleSearchItem]
    total: int
    source_mode: CatalogDataMode = "seed"


class VehicleDetailV1(StrictModel):
    vehicle: VehicleTrim
    source_mode: CatalogDataMode = "seed"
    production_ready: bool = False
    supported_domains: list[str] = Field(default_factory=lambda: ["ice_road_vehicle"])
    readiness_notes: list[ReadinessNote] = Field(default_factory=list)


class BuildAssemblyPatchRequest(StrictModel):
    parts: dict[str, str] = Field(default_factory=dict)
    scenario_name: str | None = None
    target_metrics: TargetMetrics | None = None
    tolerances: QueryTolerance | None = None
    engine_patch: PatchEngineRequest | None = None
    drivetrain_patch: PatchDrivetrainRequest | None = None


class AssemblyNode(StrictModel):
    node_id: str
    kind: Literal["vehicle", "scenario", "engine", "part"]
    subsystem: str
    label: str
    selection_id: str | None = None


class AssemblyEdge(StrictModel):
    edge_id: str
    source: str
    target: str
    relation: str
    status: FitmentStatus


class BuildAssemblyGraph(StrictModel):
    build_id: str
    build_hash: str
    nodes: list[AssemblyNode]
    edges: list[AssemblyEdge]


class SubsystemFitmentOutcome(StrictModel):
    subsystem: str
    selection_id: str | None = None
    outcome: FitmentStatus
    source_mode: CatalogDataMode = "seed"
    asset_readiness: AssetReadiness
    reasons: list[str] = Field(default_factory=list)


class BuildValidationReport(StrictModel):
    build_id: str
    build_hash: str
    source_mode: CatalogDataMode = "seed"
    build: BuildState
    assembly_graph: BuildAssemblyGraph
    validation: BuildValidationSnapshot
    subsystem_outcomes: list[SubsystemFitmentOutcome]
    production_blockers: list[str] = Field(default_factory=list)


class SceneAssetStatus(StrictModel):
    subsystem: str
    object_id: str
    asset_readiness: AssetReadiness


class BuildSceneResponse(StrictModel):
    build_id: str
    build_hash: str
    source_mode: CatalogDataMode = "seed"
    render_config: RenderConfig
    assets: list[SceneAssetStatus]


class SimulationResponse(StrictModel):
    build_id: str
    build_hash: str
    mode: SimulationMode
    source_mode: CatalogDataMode = "seed"
    calibration_state: Literal["seed_heuristic", "calibration_required", "calibrated"] = "seed_heuristic"
    payload: dict[str, Any]


class CatalogSourceContract(StrictModel):
    source_id: str
    provider: str
    contract_type: Literal["autocare", "vpic", "tecdoc", "vendor_feed", "exact_asset_manifest"]
    status: Literal["planned", "implemented_seed", "contract_defined"]
    description: str
    required_fields: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class CatalogSourceContractsResponse(StrictModel):
    items: list[CatalogSourceContract]
