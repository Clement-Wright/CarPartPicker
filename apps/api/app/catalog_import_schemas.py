from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from app.production_schemas import CatalogDataMode, ProxyGeometry, SceneDimensions, VisualizationMode
from app.schemas import (
    ChassisEnvelope,
    DrivetrainConfig,
    EngineBuildSpec,
    EngineFamily,
    PartCatalogItem,
    StrictModel,
    VehicleBaseConfig,
    VehiclePlatform,
    VehicleTrim,
)


SUPPORTED_IMPORTED_CATEGORIES = ("vehicles", "engines", "transmissions", "wheels", "tires", "brakes")
SUPPORTED_IMPORTED_PART_SUBSYSTEMS = ("transmission", "wheels", "tires", "brakes")

ImportAdapterMode = Literal["api_pull", "export_load"]
ImportRunStatus = Literal["queued", "running", "succeeded", "failed", "partial"]
ImportAttemptStatus = Literal["running", "succeeded", "failed"]
RawEntityType = Literal[
    "vehicle",
    "engine_family",
    "engine_config",
    "drivetrain_config",
    "part",
    "application",
    "price_snapshot",
]


class CatalogRecordProvenance(StrictModel):
    source_id: str
    provider: str
    source_record_id: str
    import_run_id: str
    source_mode: CatalogDataMode = "licensed"
    verification_status: Literal["verified", "licensed_sample", "seeded", "unverified"] = "licensed_sample"
    observed_at: str
    updated_at: str
    summary: str


class AssetCoverage(StrictModel):
    visualization_mode: VisualizationMode
    mesh_url: str | None = None
    proxy_geometry: ProxyGeometry | None = None
    dimensions: SceneDimensions = Field(default_factory=SceneDimensions)
    anchor_slot: str | None = None
    anchor_strategy: Literal["single", "wheel_corners", "brake_corners", "derived"] = "single"
    scene_renderable: bool = False
    catalog_visible: bool = True
    notes: list[str] = Field(default_factory=list)
    hidden_reason: str | None = None


class CanonicalPriceSnapshot(StrictModel):
    snapshot_id: str
    part_id: str
    source: str
    provider: str
    source_id: str
    source_record_id: str
    import_run_id: str
    source_mode: CatalogDataMode = "licensed"
    price_usd: float
    currency: str = "USD"
    availability: str = "unknown"
    product_url: str | None = None
    observed_at: str
    provenance_summary: str


class CanonicalPartApplication(StrictModel):
    application_id: str
    part_id: str
    vehicle_id: str
    fitment_status: Literal["direct_fit", "fits_with_adapter", "fits_with_fabrication"] = "direct_fit"
    required_mount_family: str | None = None
    required_bellhousing_family: str | None = None
    required_bolt_pattern: str | None = None
    required_hub_bore_mm: float | None = None
    minimum_wheel_diameter_in: float | None = None
    minimum_wheel_width_in: float | None = None
    minimum_tire_width_mm: float | None = None
    maximum_tire_width_mm: float | None = None
    required_drivetrain_family: str | None = None
    required_transmission_type: Literal["manual", "automatic", "any"] | None = None
    required_ecu_family: str | None = None
    required_cooling_family: str | None = None
    required_supporting_part_ids: list[str] = Field(default_factory=list)
    excluded_part_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    provenance: CatalogRecordProvenance


class CanonicalVehicleRecord(StrictModel):
    vehicle_id: str
    label: str
    source_mode: CatalogDataMode = "licensed"
    vehicle: VehicleTrim
    platform: VehiclePlatform
    chassis_envelope: ChassisEnvelope
    base_config: VehicleBaseConfig
    default_engine_config_id: str
    default_drivetrain_config_id: str
    supported_domains: list[str] = Field(default_factory=lambda: ["ice_road_vehicle"])
    scene_anchor_slots: list[str] = Field(
        default_factory=lambda: [
            "body_shell",
            "engine_bay",
            "transmission_tunnel",
            "front_left_hub",
            "front_right_hub",
            "rear_left_hub",
            "rear_right_hub",
            "front_left_brake",
            "front_right_brake",
            "rear_left_brake",
            "rear_right_brake",
        ]
    )
    provenance: CatalogRecordProvenance


class CanonicalEngineFamilyRecord(StrictModel):
    engine_family_id: str
    source_mode: CatalogDataMode = "licensed"
    engine_family: EngineFamily
    provenance: CatalogRecordProvenance


class CanonicalEngineConfigRecord(StrictModel):
    config_id: str
    source_mode: CatalogDataMode = "licensed"
    engine_config: EngineBuildSpec
    provenance: CatalogRecordProvenance


class CanonicalDrivetrainRecord(StrictModel):
    config_id: str
    source_mode: CatalogDataMode = "licensed"
    drivetrain_config: DrivetrainConfig
    provenance: CatalogRecordProvenance


class CanonicalPartRecord(StrictModel):
    part_id: str
    subsystem: str
    label: str
    source_mode: CatalogDataMode = "licensed"
    part: PartCatalogItem
    applications: list[CanonicalPartApplication] = Field(default_factory=list)
    prices: list[CanonicalPriceSnapshot] = Field(default_factory=list)
    asset_coverage: AssetCoverage
    provenance: CatalogRecordProvenance
    supported_slice: bool = True


class CatalogImportRun(StrictModel):
    import_run_id: str
    source_id: str
    provider: str
    adapter_mode: ImportAdapterMode
    status: ImportRunStatus = "queued"
    categories: list[str] = Field(default_factory=lambda: list(SUPPORTED_IMPORTED_CATEGORIES))
    requested_at: str
    started_at: str | None = None
    completed_at: str | None = None
    raw_record_count: int = 0
    normalized_record_count: int = 0
    error_count: int = 0
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogImportAttempt(StrictModel):
    attempt_id: str
    import_run_id: str
    adapter_mode: ImportAdapterMode
    status: ImportAttemptStatus = "running"
    started_at: str
    completed_at: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RawSourceEnvelope(StrictModel):
    entity_type: RawEntityType
    source_id: str
    provider: str
    source_record_id: str
    observed_at: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)


class RawSourcePayloadRecord(StrictModel):
    payload_id: str
    import_run_id: str
    attempt_id: str
    entity_type: RawEntityType
    source_id: str
    provider: str
    source_record_id: str
    observed_at: str
    payload: dict[str, Any]
    payload_hash: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CatalogImportTriggerRequest(StrictModel):
    source_id: str = "licensed_fixture_catalog"
    adapter_mode: ImportAdapterMode = "export_load"
    force_reimport: bool = False


class CatalogImportRunResponse(StrictModel):
    run: CatalogImportRun
    attempts: list[CatalogImportAttempt] = Field(default_factory=list)
    raw_payloads: int = 0
    normalized_entities: dict[str, int] = Field(default_factory=dict)

