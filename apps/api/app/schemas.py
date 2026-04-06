from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FactProvenance(StrictModel):
    source: str
    confidence: float = 0.8
    basis: str
    last_verified: str
    kind: Literal["manufacturer", "nhtsa", "hand_curated", "inferred", "simulated"]


class IngestLineage(StrictModel):
    source_system: str
    source_record_id: str
    import_batch_id: str
    verification_status: Literal["verified", "seeded", "inferred", "unverified"] = "seeded"
    measurement_basis: str


class ImportBatch(StrictModel):
    import_batch_id: str
    source_system: str
    imported_at: str
    status: Literal["seeded", "pending", "complete"] = "seeded"
    record_count: int = 0
    notes: str = ""


class VehicleContext(StrictModel):
    trim_id: str | None = None
    year: int | None = None
    make: str | None = None
    model: str | None = None
    trim: str | None = None


class QueryTolerance(StrictModel):
    allow_fabrication: bool = False
    keep_street_legal: bool = True
    protect_daily_comfort: bool = True


class TargetMetrics(StrictModel):
    budget_max: float | None = None
    hp_min: float | None = None
    torque_min: float | None = None
    weight_max_lb: float | None = None
    redline_min_rpm: int | None = None
    top_speed_min_mph: float | None = None
    zero_to_sixty_max_s: float | None = None
    braking_distance_max_ft: float | None = None


class SimilarityRequest(StrictModel):
    reference_vehicle: str | None = None
    attributes: list[str] = Field(default_factory=list)


class ParsedTargetSpec(StrictModel):
    text: str
    budget_max: float | None = None
    target_metrics: TargetMetrics = Field(default_factory=TargetMetrics)
    hard_constraints: dict[str, list[str]] = Field(default_factory=dict)
    soft_similarity: SimilarityRequest = Field(default_factory=SimilarityRequest)
    use_cases: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    fabrication_tolerance: Literal["low", "medium", "high"] = "low"
    legal_tolerance: Literal["strict", "flexible"] = "strict"
    confidence: float = 0.0


class DecodeVinRequest(StrictModel):
    vin: str


class DecodedVehicle(StrictModel):
    vin: str
    trim_id: str | None = None
    year: int | None = None
    make: str | None = None
    model: str | None = None
    trim: str | None = None
    source: str
    cache_hit: bool


class BoundingEnvelope(StrictModel):
    length_mm: float = 0.0
    width_mm: float = 0.0
    height_mm: float = 0.0


class ClearanceZone(StrictModel):
    zone_id: str
    label: str
    envelope: BoundingEnvelope = Field(default_factory=BoundingEnvelope)
    required_clearance_mm: float = 0.0
    available_clearance_mm: float = 0.0


class WheelBarrelProfile(StrictModel):
    profile_id: str
    min_brake_diameter_in: float
    barrel_width_in: float


class BrakeEnvelope(StrictModel):
    envelope_id: str
    minimum_wheel_diameter_in: float
    radial_clearance_mm: float


class TireSweepEnvelope(StrictModel):
    envelope_id: str
    nominal_width_mm: float
    rub_risk: float = 0.0
    full_lock_margin_mm: float = 0.0


class RideHeightTravelEnvelope(StrictModel):
    envelope_id: str
    nominal_drop_mm: float = 0.0
    safe_compression_margin_mm: float = 0.0


class MountInterface(StrictModel):
    mount_family: str | None = None


class BellhousingInterface(StrictModel):
    bellhousing_family: str | None = None


class CoolingInterface(StrictModel):
    cooling_family: str | None = None
    cooling_load_index: float = 0.0


class DrivelineInterface(StrictModel):
    drivetrain_family: str | None = None
    axle_family: str | None = None


class ElectricalInterface(StrictModel):
    ecu_family: str | None = None
    harness_family: str | None = None


class FabricationRequirement(StrictModel):
    fabrication_id: str
    label: str
    detail: str
    severity: Literal["minor", "moderate", "major"] = "minor"


class PartInterface(StrictModel):
    transmission_type: Literal["manual", "automatic", "any"] = "any"
    drivetrain_family: str | None = None
    bellhousing_family: str | None = None
    ecu_family: str | None = None
    wheel_bolt_pattern: str | None = None
    hub_bore_mm: float | None = None
    mount_family: str | None = None
    electrical_family: str | None = None


class GeometryProfile(StrictModel):
    wheel_diameter_in: float | None = None
    wheel_width_in: float | None = None
    tire_width_mm: float | None = None
    brake_min_wheel_in: float | None = None
    hood_clearance_needed_mm: float = 0.0
    hood_clearance_gain_mm: float = 0.0
    ride_height_drop_mm: float = 0.0
    tire_rub_risk: float = 0.0
    thermal_load: float = 0.0
    barrel_profile: str | None = None
    brake_envelope: str | None = None
    engine_bay_margin_mm: float = 0.0
    tire_sweep_margin_mm: float = 0.0
    fabrication_zones: list[str] = Field(default_factory=list)


class PerformanceDelta(StrictModel):
    hp_delta: float = 0.0
    torque_delta: float = 0.0
    weight_delta_lb: float = 0.0
    cooling_delta: float = 0.0
    braking_delta: float = 0.0
    grip_delta: float = 0.0
    drag_delta: float = 0.0
    downforce_delta: float = 0.0
    comfort_delta: float = 0.0
    driveline_stress_delta: float = 0.0
    thermal_delta: float = 0.0
    redline_delta_rpm: int = 0


ValidationSeverity = Literal[
    "BLOCKER",
    "WARNING",
    "SCENARIO_PENALTY",
    "FABRICATION_REQUIRED",
    "UNKNOWN",
]


class DependencyRule(StrictModel):
    kind: Literal[
        "requires_part",
        "requires_one_of",
        "blocks_scenario",
        "needs_fabrication",
        "torque_limit",
        "geometry_gate",
        "requires_engine_family",
    ]
    message: str
    subsystem: str | None = None
    required_part_ids: list[str] = Field(default_factory=list)
    required_config_ids: list[str] = Field(default_factory=list)
    minimum_value: float | None = None
    severity: ValidationSeverity = "BLOCKER"
    provenance: FactProvenance


class VisualAsset(StrictModel):
    slot: str
    kind: str
    color: str = "#b6c2cf"
    scale: tuple[float, float, float] = (1.0, 1.0, 1.0)
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    visible: bool = True


class VehiclePlatform(StrictModel):
    platform_id: str
    label: str
    manufacturer: str
    drivetrain_layout: str
    stock_mount_family: str
    stock_bellhousing_family: str
    stock_ecu_family: str
    stock_cooling_family: str
    stock_driveline_family: str
    wheel_bolt_pattern: str
    hub_bore_mm: float
    lineage: IngestLineage
    provenance: FactProvenance


class ChassisEnvelope(StrictModel):
    platform_id: str
    engine_bay: BoundingEnvelope
    transmission_tunnel: BoundingEnvelope
    ride_height_travel: RideHeightTravelEnvelope
    front_tire_sweep: TireSweepEnvelope
    wheel_barrel_profile: WheelBarrelProfile
    stock_brake_envelope: BrakeEnvelope


class EngineEnvelope(StrictModel):
    length_mm: float
    width_mm: float
    height_mm: float


class EngineArchitecture(StrictModel):
    architecture_id: str
    label: str
    layout: Literal["flat4", "inline4", "inline6", "v6", "v8"]
    cylinder_count: int
    head_type: str
    valves_per_cylinder: int
    valvetrain: str


class CamProfileSpec(StrictModel):
    profile_id: str
    label: str
    intake_bias: float = 0.0
    exhaust_bias: float = 0.0
    top_end_bias: float = 0.0
    low_end_bias: float = 0.0


class ValveTrainSpec(StrictModel):
    label: str
    head_flow_stage: Literal["stock", "street", "race"] = "stock"
    valves_per_cylinder: int
    variable_valve_timing: bool = True


class InductionSpec(StrictModel):
    type: Literal["na", "turbo", "supercharger"] = "na"
    boost_psi: float = 0.0
    intercooler_required: bool = False


class FuelSpec(StrictModel):
    fuel_type: Literal["91_octane", "93_octane", "e85"] = "93_octane"
    injector_scale: Literal["stock", "upgrade", "high_flow"] = "stock"
    pump_scale: Literal["stock", "upgrade", "high_flow"] = "stock"


class ExhaustSpec(StrictModel):
    exhaust_style: Literal["stock", "catback", "turbo_back", "equal_length"] = "stock"
    flow_bias: float = 0.0
    noise_bias: float = 0.0


class EngineFamily(StrictModel):
    engine_family_id: str
    label: str
    architecture: EngineArchitecture
    base_displacement_l: float
    base_weight_lb: float
    base_peak_hp: float
    base_peak_torque_lbft: float
    base_redline_rpm: int
    stock_bore_mm: float
    stock_stroke_mm: float
    compression_ratio: float
    mount_interface: MountInterface
    bellhousing_interface: BellhousingInterface
    cooling_interface: CoolingInterface
    driveline_interface: DrivelineInterface
    electrical_interface: ElectricalInterface
    envelope: EngineEnvelope
    fabrication_requirements: list[FabricationRequirement] = Field(default_factory=list)
    required_supporting_part_ids: list[str] = Field(default_factory=list)
    required_visual_slots: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    lineage: IngestLineage
    provenance: FactProvenance


class EngineBuildSpec(StrictModel):
    config_id: str
    engine_family_id: str
    label: str
    cylinder_count: int
    layout: str
    bore_mm: float
    stroke_mm: float
    compression_ratio: float
    rod_length_mm: float = 128.0
    valve_train: ValveTrainSpec
    cam_profile: CamProfileSpec
    intake_cam_duration_deg: float = 252.0
    exhaust_cam_duration_deg: float = 248.0
    intake_lift_mm: float = 10.4
    exhaust_lift_mm: float = 10.0
    lobe_separation_deg: float = 112.0
    induction: InductionSpec
    compressor_efficiency: float = 0.72
    intercooler_effectiveness: float = 0.78
    fuel: FuelSpec
    target_lambda: float = 0.88
    ignition_advance_bias_deg: float = 0.0
    exhaust: ExhaustSpec
    exhaust_backpressure_factor: float = 1.0
    tune_bias: Literal["comfort", "balanced", "aggressive"] = "balanced"
    rev_limit_rpm: int
    radiator_effectiveness: float = 0.85
    ambient_temp_c: float = 20.0
    altitude_m: float = 0.0
    notes: list[str] = Field(default_factory=list)


class DrivetrainConfig(StrictModel):
    config_id: str
    label: str
    transmission_mode: Literal["manual", "automatic"]
    gear_ratios: list[float] = Field(default_factory=list)
    final_drive_ratio: float
    driveline_loss_factor: float = 0.13
    differential_bias: Literal["street_lsd", "track_lsd", "open", "torsen"] = "street_lsd"
    shift_latency_ms: int = 180


class PartCatalogItem(StrictModel):
    part_id: str
    subsystem: str
    label: str
    brand: str
    notes: str
    cost_usd: int
    compatible_platforms: list[str]
    compatible_transmissions: list[Literal["manual", "automatic", "any"]] = Field(
        default_factory=lambda: ["any"]
    )
    tags: list[str] = Field(default_factory=list)
    interface: PartInterface = Field(default_factory=PartInterface)
    geometry: GeometryProfile = Field(default_factory=GeometryProfile)
    performance: PerformanceDelta = Field(default_factory=PerformanceDelta)
    capabilities: dict[str, float] = Field(default_factory=dict)
    dependency_rules: list[DependencyRule] = Field(default_factory=list)
    visual: VisualAsset
    lineage: IngestLineage
    provenance: FactProvenance


class StockPartReference(StrictModel):
    subsystem: str
    stock_part_id: str


class StockConfigReference(StrictModel):
    subsystem: str
    stock_config_id: str


class SubsystemSlotDefinition(StrictModel):
    subsystem: str
    label: str
    description: str
    stock_part_id: str | None = None
    stock_config_id: str | None = None


class VehicleBaseConfig(StrictModel):
    config_id: str
    trim_id: str
    subsystem_slots: list[SubsystemSlotDefinition]
    stock_parts: list[StockPartReference]
    stock_configs: list[StockConfigReference] = Field(default_factory=list)


class BuildPreset(StrictModel):
    preset_id: str
    title: str
    description: str
    scenario_name: str
    tags: list[str] = Field(default_factory=list)
    patch: dict[str, str]
    provenance: FactProvenance


class BuildSubsystemSelection(StrictModel):
    subsystem: str
    selected_part_id: str | None = None
    selected_config_id: str | None = None
    source: Literal["stock", "preset", "manual"] = "stock"

    @model_validator(mode="after")
    def ensure_one_selection(self) -> "BuildSubsystemSelection":
        if bool(self.selected_part_id) == bool(self.selected_config_id):
            raise ValueError("Exactly one of selected_part_id or selected_config_id must be set.")
        return self


class BuildComputationVersion(StrictModel):
    build_hash: str
    revision: int
    updated_at: datetime


class BuildState(StrictModel):
    build_id: str
    vehicle: VehicleTrim
    vehicle_platform: VehiclePlatform
    chassis_envelope: ChassisEnvelope
    base_config: VehicleBaseConfig
    active_scenario: str
    target_metrics: TargetMetrics = Field(default_factory=TargetMetrics)
    tolerances: QueryTolerance = Field(default_factory=QueryTolerance)
    selections: list[BuildSubsystemSelection]
    engine_build_spec: EngineBuildSpec
    drivetrain_config: DrivetrainConfig
    computation: BuildComputationVersion
    active_notes: list[str] = Field(default_factory=list)


class ValidationFinding(StrictModel):
    finding_id: str
    phase: Literal["fast", "heavy"]
    category: Literal["interface", "geometry", "dependency", "scenario"]
    severity: ValidationSeverity
    subsystem: str
    title: str
    detail: str
    blocking: bool = False
    related_parts: list[str] = Field(default_factory=list)
    related_configs: list[str] = Field(default_factory=list)
    provenance: FactProvenance


class ValidationSummary(StrictModel):
    blockers: int = 0
    warnings: int = 0
    scenario_penalties: int = 0
    fabrication_required: int = 0
    unknown: int = 0


class BuildValidationSnapshot(StrictModel):
    build_id: str
    build_hash: str
    phase: Literal["fast", "heavy"]
    summary: ValidationSummary
    findings: list[ValidationFinding]
    computed_at: datetime


class DerivedMetricSet(StrictModel):
    peak_hp: float
    peak_torque_lbft: float
    curb_weight_lb: float
    upgrade_cost_usd: float
    redline_rpm: int
    power_to_weight_hp_per_ton: float
    top_speed_mph: float
    zero_to_sixty_s: float
    quarter_mile_s: float
    braking_distance_ft: float
    lateral_grip_g: float
    thermal_headroom: float
    driveline_stress: float
    comfort_index: float
    fabrication_index: float
    budget_remaining_usd: float | None = None


class VehicleMetricSnapshot(StrictModel):
    build_id: str
    build_hash: str
    metrics: DerivedMetricSet
    computed_at: datetime
    provenance: FactProvenance


class BuildMetricSnapshot(VehicleMetricSnapshot):
    pass


class DynoCurvePoint(StrictModel):
    rpm: int
    torque_lbft: float
    hp: float


class GearCurvePoint(StrictModel):
    rpm: int
    speed_mph: float
    wheel_torque_lbft: float


class GearCurve(StrictModel):
    gear: str
    points: list[GearCurvePoint]


class DynoResult(StrictModel):
    peak_hp: float
    peak_torque_lbft: float
    shift_rpm: int
    engine_curve: list[DynoCurvePoint]
    gear_curves: list[GearCurve]


class EngineSimulationSnapshot(StrictModel):
    build_id: str
    build_hash: str
    engine_family_id: str
    spec_hash: str
    dyno: DynoResult
    computed_at: datetime
    provenance: FactProvenance
    model_version: str = "dyno_lite_v1"
    derived_values: dict[str, Any] = Field(default_factory=dict)
    limiting_factors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    explanation_summary: str = ""


class BuildDynoSnapshot(EngineSimulationSnapshot):
    pass


class ScenarioResult(StrictModel):
    scenario_name: str
    score: float
    passing: bool
    strengths: list[str] = Field(default_factory=list)
    penalties: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class BuildScenarioSnapshot(StrictModel):
    build_id: str
    build_hash: str
    result: ScenarioResult
    computed_at: datetime
    provenance: FactProvenance


class RenderSceneObject(StrictModel):
    object_id: str
    slot: str
    kind: str
    color: str
    position: tuple[float, float, float]
    scale: tuple[float, float, float]
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)
    visible: bool = True
    highlight: Literal["none", "warning", "error"] = "none"


class RenderHighlight(StrictModel):
    zone: str
    severity: Literal["warning", "error"]
    message: str


class RenderConfig(StrictModel):
    build_id: str
    build_hash: str
    ride_height_drop_mm: float
    paint_color: str
    scene_objects: list[RenderSceneObject]
    highlights: list[RenderHighlight] = Field(default_factory=list)
    computed_at: datetime


class GraphNode(StrictModel):
    id: str
    label: str
    kind: str
    status: Literal["info", "positive", "warning", "conflict"]
    description: str
    position: dict[str, float]


class GraphEdge(StrictModel):
    id: str
    source: str
    target: str
    label: str
    status: Literal["info", "positive", "warning", "conflict"]


class GraphResponse(StrictModel):
    build_id: str
    build_hash: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    highlights: list[str]
    findings: list[str] = Field(default_factory=list)


class SlotDiff(StrictModel):
    subsystem: str
    stock_part_id: str | None = None
    stock_config_id: str | None = None
    baseline_part_id: str | None = None
    baseline_config_id: str | None = None
    current_part_id: str | None = None
    current_config_id: str | None = None
    changed: bool


class VehicleTrim(StrictModel):
    trim_id: str
    platform: str
    year: int
    make: str
    model: str
    trim: str
    drivetrain: str
    transmission: str
    body_style: str
    stock_wheel_diameter: int
    stock_tire: str
    stock_hp: float
    stock_torque_lbft: float
    stock_weight_lb: float
    redline_rpm: int
    stock_zero_to_sixty_s: float
    stock_top_speed_mph: float
    stock_braking_distance_ft: float
    stock_lateral_grip_g: float
    stock_thermal_headroom: float
    stock_comfort_index: float
    stock_drag_index: float
    stock_downforce_index: float
    driveline_limit_lbft: float
    gear_ratios: list[float] = Field(default_factory=list)
    final_drive_ratio: float
    safety_index: float
    recall_burden: float
    complaint_burden: float
    recall_summary: str
    complaint_summary: str
    utility_note: str
    mod_potential: float
    provenance: FactProvenance


class VehicleSummary(StrictModel):
    trim_id: str
    label: str
    platform: str
    stock_wheel_diameter: int
    transmission: str


class VehicleDetail(StrictModel):
    trim: VehicleTrim
    safety_context: dict[str, Any]


class ScenarioDefinition(StrictModel):
    scenario_name: str
    label: str
    description: str
    weights: dict[str, float] = Field(default_factory=dict)
    gates: list[str] = Field(default_factory=list)
    penalties: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class BuildDiffResponse(StrictModel):
    build_id: str
    against: str
    slots: list[SlotDiff]


class BuildDetailResponse(StrictModel):
    build: BuildState
    available_parts: dict[str, list[PartCatalogItem]]
    available_presets: list[BuildPreset]
    scenario_definitions: list[ScenarioDefinition]
    engine_families: list[EngineFamily]
    import_batches: list[ImportBatch]


class CreateBuildRequest(StrictModel):
    trim_id: str | None = None
    vin: str | None = None
    scenario_name: str = "daily"
    target_metrics: TargetMetrics = Field(default_factory=TargetMetrics)
    tolerances: QueryTolerance = Field(default_factory=QueryTolerance)


class PatchBuildPartsRequest(StrictModel):
    parts: dict[str, str] = Field(default_factory=dict)
    scenario_name: str | None = None
    target_metrics: TargetMetrics | None = None
    tolerances: QueryTolerance | None = None


class PatchEngineRequest(StrictModel):
    engine_family_id: str | None = None
    label: str | None = None
    cylinder_count: int | None = None
    layout: str | None = None
    bore_mm: float | None = None
    stroke_mm: float | None = None
    compression_ratio: float | None = None
    rod_length_mm: float | None = None
    head_flow_stage: Literal["stock", "street", "race"] | None = None
    valves_per_cylinder: int | None = None
    variable_valve_timing: bool | None = None
    cam_profile_id: str | None = None
    intake_cam_duration_deg: float | None = None
    exhaust_cam_duration_deg: float | None = None
    intake_lift_mm: float | None = None
    exhaust_lift_mm: float | None = None
    lobe_separation_deg: float | None = None
    induction_type: Literal["na", "turbo", "supercharger"] | None = None
    boost_psi: float | None = None
    compressor_efficiency: float | None = None
    intercooler_effectiveness: float | None = None
    fuel_type: Literal["91_octane", "93_octane", "e85"] | None = None
    injector_scale: Literal["stock", "upgrade", "high_flow"] | None = None
    pump_scale: Literal["stock", "upgrade", "high_flow"] | None = None
    target_lambda: float | None = None
    ignition_advance_bias_deg: float | None = None
    exhaust_style: Literal["stock", "catback", "turbo_back", "equal_length"] | None = None
    exhaust_backpressure_factor: float | None = None
    tune_bias: Literal["comfort", "balanced", "aggressive"] | None = None
    rev_limit_rpm: int | None = None
    radiator_effectiveness: float | None = None
    ambient_temp_c: float | None = None
    altitude_m: float | None = None


class PatchDrivetrainRequest(StrictModel):
    label: str | None = None
    transmission_mode: Literal["manual", "automatic"] | None = None
    gear_ratios: list[float] | None = None
    final_drive_ratio: float | None = None
    driveline_loss_factor: float | None = None
    differential_bias: Literal["street_lsd", "track_lsd", "open", "torsen"] | None = None
    shift_latency_ms: int | None = None


class CloneBuildResponse(StrictModel):
    build_id: str
    source_build_id: str


class PresetApplicationResponse(StrictModel):
    build: BuildState
    applied_preset: BuildPreset


class TargetSpecRequest(StrictModel):
    text: str


class TargetSpecCandidate(StrictModel):
    title: str
    trim_id: str
    preset_id: str | None = None
    score: float
    why: list[str]
    estimated_metrics: DerivedMetricSet
    scenario_name: str
    create_payload: CreateBuildRequest
    preset_payload: dict[str, str] = Field(default_factory=dict)


class TargetSpecResponse(StrictModel):
    parsed: ParsedTargetSpec
    candidates: list[TargetSpecCandidate]


class CatalogImportRequest(StrictModel):
    source_system: str = "seed_catalog"
    import_scope: Literal["seed_engine_families", "seed_parts", "seed_all"] = "seed_all"


class CatalogImportResponse(StrictModel):
    import_batch: ImportBatch
    imported_entities: dict[str, int]
    notes: list[str] = Field(default_factory=list)
