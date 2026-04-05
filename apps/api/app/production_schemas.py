from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from app.schemas import (
    BuildState,
    BuildValidationSnapshot,
    PatchDrivetrainRequest,
    PatchEngineRequest,
    QueryTolerance,
    StrictModel,
    TargetMetrics,
    VehicleTrim,
)


CatalogDataMode = Literal["seed", "licensed", "verified"]
VisualizationMode = Literal["exact_mesh_ready", "proxy_from_dimensions", "catalog_only", "unsupported"]
RenderableAssetMode = Literal["exact_mesh_ready", "proxy_from_dimensions"]
OmittedAssetMode = Literal["catalog_only", "unsupported"]
FitmentStatus = Literal["direct_fit", "fits_with_adapter", "fits_with_fabrication", "simulation_only", "invalid"]
SimulationMode = Literal["engine", "vehicle", "thermal", "braking", "handling"]


class ReadinessNote(StrictModel):
    code: str
    message: str


class ProxyGeometry(StrictModel):
    kind: Literal["box", "cylinder", "disc"]
    color: str = "#9aa8b3"
    size_mm: tuple[float, float, float] | None = None
    radius_mm: float | None = None
    width_mm: float | None = None
    thickness_mm: float | None = None
    length_mm: float | None = None


class SceneDimensions(StrictModel):
    length_mm: float = 0.0
    width_mm: float = 0.0
    height_mm: float = 0.0


class SceneTransform(StrictModel):
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)


class SceneAnchor(StrictModel):
    slot: str
    zone: str | None = None


class SceneHighlight(StrictModel):
    zone: str
    severity: Literal["warning", "error"]
    message: str


class VisualizationSummary(StrictModel):
    exact_mesh_ready: int = 0
    proxy_from_dimensions: int = 0
    catalog_only: int = 0
    unsupported: int = 0
    renderable_count: int = 0
    catalog_visible_count: int = 0


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
    visualization_mode: VisualizationMode
    has_exact_mesh: bool = False
    has_proxy_geometry: bool = False
    has_dimensional_specs: bool = False
    scene_renderable: bool = False
    catalog_visible: bool = True
    geometry: dict[str, Any] = Field(default_factory=dict)
    performance: dict[str, Any] = Field(default_factory=dict)
    visualization_notes: list[ReadinessNote] = Field(default_factory=list)


class PartDetailV1(PartSummaryV1):
    compatible_platforms: list[str] = Field(default_factory=list)
    compatible_transmissions: list[str] = Field(default_factory=list)
    interface: dict[str, Any] = Field(default_factory=dict)
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
    visualization_mode: VisualizationMode
    scene_renderable: bool = False
    catalog_visible: bool = True
    reasons: list[str] = Field(default_factory=list)
    support_notes: list[ReadinessNote] = Field(default_factory=list)


class BuildValidationReport(StrictModel):
    build_id: str
    build_hash: str
    source_mode: CatalogDataMode = "seed"
    build: BuildState
    assembly_graph: BuildAssemblyGraph
    validation: BuildValidationSnapshot
    subsystem_outcomes: list[SubsystemFitmentOutcome]
    visualization_summary: VisualizationSummary = Field(default_factory=VisualizationSummary)
    support_notes: list[str] = Field(default_factory=list)


class SceneItem(StrictModel):
    part_id: str
    instance_id: str
    subsystem: str
    asset_mode: RenderableAssetMode
    mesh_url: str | None = None
    proxy_geometry: ProxyGeometry | None = None
    dimensions: SceneDimensions = Field(default_factory=SceneDimensions)
    transform: SceneTransform = Field(default_factory=SceneTransform)
    anchor: SceneAnchor
    hidden_reason: str | None = None


class OmittedSceneItem(StrictModel):
    part_id: str
    subsystem: str
    asset_mode: OmittedAssetMode
    hidden_reason: str


class SceneSummary(StrictModel):
    renderable_count: int = 0
    exact_count: int = 0
    proxy_count: int = 0
    omitted_count: int = 0


class BuildSceneResponse(StrictModel):
    build_id: str
    build_hash: str
    source_mode: CatalogDataMode = "seed"
    items: list[SceneItem] = Field(default_factory=list)
    omitted_items: list[OmittedSceneItem] = Field(default_factory=list)
    highlights: list[SceneHighlight] = Field(default_factory=list)
    summary: SceneSummary = Field(default_factory=SceneSummary)


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
