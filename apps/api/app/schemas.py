from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CurrentSetup(StrictModel):
    wheel_diameter: int | None = None
    keep_current_wheels: bool = False
    notes: list[str] = Field(default_factory=list)


class VehicleContext(StrictModel):
    trim_id: str | None = None
    year: int | None = None
    make: str | None = None
    model: str | None = None
    trim: str | None = None


class QueryParseRequest(StrictModel):
    text: str
    mode: Literal["build_path"] = "build_path"
    vehicle_context: VehicleContext | None = None


class ParsedBuildQuery(StrictModel):
    goals: list[str] = Field(default_factory=list)
    budget_max: int | None = None
    hard_constraints: list[str] = Field(default_factory=list)
    current_setup: CurrentSetup | None = None
    confidence: float
    extracted_terms: list[str] = Field(default_factory=list)


class PriceBand(StrictModel):
    min: int
    max: int


class PartSeed(StrictModel):
    part_id: str
    category: str
    brand: str
    name: str
    platforms: list[str]
    wheel_diameter: int | None = None
    requires_min_wheel_diameter: int | None = None
    season: str = "all"
    comfort_bias: float = 0.0
    grip_bias: float = 0.0
    winter_bias: float = 0.0
    braking_bias: float = 0.0
    safety_delta: float = 0.0
    cost: int
    notes: str


class RuleSeed(StrictModel):
    kind: str
    value: float | int | None = None
    message: str


class AxisBundle(StrictModel):
    safety: float
    fun: float
    utility: float
    cost: float
    mod_potential: float
    winter: float


class PackageSeed(StrictModel):
    package_id: str
    title: str
    subtitle: str
    description: str
    compatible_platforms: list[str]
    compatible_trim_ids: list[str]
    goal_biases: dict[str, float]
    axes: AxisBundle
    effect_tags: list[str]
    price_band: PriceBand
    part_ids: list[str]
    supporting_parts: list[str]
    required_conditions: list[RuleSeed] = Field(default_factory=list)
    blocked_conditions: list[RuleSeed] = Field(default_factory=list)
    dependency_count: int
    fitment_base: float
    safety_preservation: float
    tradeoff_notes: list[str]
    what_changes: list[str]


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
    safety_index: float
    recall_burden: float
    complaint_burden: float
    recall_summary: str
    complaint_summary: str
    utility_note: str
    mod_potential: float


class VehicleSummary(StrictModel):
    trim_id: str
    label: str
    stock_wheel_diameter: int
    platform: str


class VehicleDetail(StrictModel):
    trim: VehicleTrim
    safety_context: dict[str, Any]


class ScoreBreakdown(StrictModel):
    goal_alignment: float
    fitment_confidence: float
    cost_efficiency: float
    safety_preservation: float
    dependency_simplicity: float
    conflict_penalty: float


class BuildRecommendationRequest(StrictModel):
    trim_id: str
    query: ParsedBuildQuery | None = None
    selected_goals: list[str] = Field(default_factory=list)
    budget_max: int | None = None
    current_setup: CurrentSetup | None = None


class BuildRecommendation(StrictModel):
    package_id: str
    title: str
    subtitle: str
    description: str
    score: float
    score_breakdown: ScoreBreakdown
    matched_goals: list[str]
    required_changes: list[str]
    conflicts: list[str]
    cost_band: PriceBand
    effect_tags: list[str]
    compatibility_status: str
    fitment_confidence: float
    safety_context: dict[str, Any]
    why_it_matched: list[str]
    explanation: str
    what_would_change: list[str]
    graph_id: str


class CompareRequest(StrictModel):
    trim_id: str
    package_ids: list[str] = Field(min_length=2, max_length=3)


class ComparePackageSummary(StrictModel):
    package_id: str
    title: str
    subtitle: str
    axes: AxisBundle
    cost_band: PriceBand
    fitment_confidence: float
    effect_tags: list[str]
    tradeoffs: list[str]


class CompareResponse(StrictModel):
    axes: list[str]
    package_summaries: list[ComparePackageSummary]
    deltas: dict[str, dict[str, float]]
    explanation_facts: dict[str, Any]


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


class EliminatedOption(StrictModel):
    package_id: str
    title: str
    reason: str


class GraphResponse(StrictModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    highlights: list[str]
    eliminated_options: list[EliminatedOption]


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
