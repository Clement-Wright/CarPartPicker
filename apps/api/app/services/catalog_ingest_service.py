from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.catalog_import_schemas import (
    AssetCoverage,
    CanonicalDrivetrainRecord,
    CanonicalEngineConfigRecord,
    CanonicalEngineFamilyRecord,
    CanonicalPartApplication,
    CanonicalPartRecord,
    CanonicalPriceSnapshot,
    CanonicalVehicleRecord,
    CatalogImportAttempt,
    CatalogImportRun,
    CatalogImportRunResponse,
    CatalogImportTriggerRequest,
    CatalogRecordProvenance,
    RawSourceEnvelope,
    RawSourcePayloadRecord,
)
from app.config import get_settings
from app.production_schemas import ProxyGeometry, SceneDimensions
from app.schemas import (
    CamProfileSpec,
    CatalogImportRequest,
    CatalogImportResponse,
    ChassisEnvelope,
    DependencyRule,
    DrivetrainConfig,
    EngineBuildSpec,
    EngineFamily,
    ExhaustSpec,
    FactProvenance,
    FuelSpec,
    ImportBatch,
    IngestLineage,
    InductionSpec,
    PartCatalogItem,
    StockConfigReference,
    StockPartReference,
    SubsystemSlotDefinition,
    ValveTrainSpec,
    VehicleBaseConfig,
    VehiclePlatform,
    VehicleTrim,
)
from app.services.catalog_index_service import get_catalog_index
from app.services.catalog_store_service import get_catalog_store


FIXTURE_SOURCE_ID = "licensed_fixture_catalog"
FIXTURE_PROVIDER = "Licensed Fixture Source"
FIXTURE_FILE = "common.json"
DEFAULT_IMPORT_NOTES = [
    "Fixture-backed licensed-source ingest is active for the supported slice.",
    "The importer contract supports both API pull and export-load modes against the same normalization path.",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _fixture_path() -> Path:
    settings = get_settings()
    return settings.seed_dir.parent / "importers" / FIXTURE_SOURCE_ID / FIXTURE_FILE


def _load_fixture_payload() -> dict[str, Any]:
    with _fixture_path().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _stable_hash(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(blob.encode("utf-8")).hexdigest()


def _build_lineage(source_record_id: str, import_run_id: str) -> IngestLineage:
    return IngestLineage(
        source_system=FIXTURE_SOURCE_ID,
        source_record_id=source_record_id,
        import_batch_id=import_run_id,
        verification_status="unverified",
        measurement_basis="normalized from licensed fixture adapter",
    )


def _build_fact_provenance(source_record_id: str, observed_at: str, basis: str) -> FactProvenance:
    return FactProvenance(
        source=f"{FIXTURE_PROVIDER}:{source_record_id}",
        confidence=0.84,
        basis=basis,
        last_verified=observed_at[:10],
        kind="hand_curated",
    )


def _record_provenance(
    *,
    source_record_id: str,
    import_run_id: str,
    observed_at: str,
    summary: str,
) -> CatalogRecordProvenance:
    return CatalogRecordProvenance(
        source_id=FIXTURE_SOURCE_ID,
        provider=FIXTURE_PROVIDER,
        source_record_id=source_record_id,
        import_run_id=import_run_id,
        verification_status="licensed_sample",
        observed_at=observed_at,
        updated_at=_now_iso(),
        summary=summary,
    )


def _vehicle_slot_map(payload: dict[str, Any]) -> dict[str, str]:
    stock_trans = payload["defaults"]["transmission_part_id"]
    stock_brakes = payload["defaults"]["brake_part_id"]
    stock_wheels = payload["defaults"]["wheel_part_id"]
    stock_tires = payload["defaults"]["tire_part_id"]
    stock_clutch = "clutch_stock" if payload["vehicle"]["transmission"] == "manual" else "clutch_not_applicable"
    return {
        "body_aero": "body_stock",
        "forced_induction": "fi_na_stock",
        "intake": "intake_stock",
        "exhaust": "exhaust_stock",
        "cooling": "cooling_stock",
        "fuel_system": "fuel_stock",
        "tune": "tune_stock",
        "transmission": stock_trans,
        "clutch": stock_clutch,
        "differential": "diff_stock",
        "suspension": "suspension_stock",
        "brakes": stock_brakes,
        "wheels": stock_wheels,
        "tires": stock_tires,
    }


def _base_config_for_vehicle(trim_id: str, payload: dict[str, Any]) -> VehicleBaseConfig:
    slot_map = _vehicle_slot_map(payload)
    subsystem_slots = [
        SubsystemSlotDefinition(
            subsystem="engine",
            label="Engine Family",
            description="Editable imported engine build specification for the current chassis.",
            stock_config_id=payload["defaults"]["engine_config_id"],
        )
    ]
    subsystem_slots.extend(
        SubsystemSlotDefinition(
            subsystem=subsystem,
            label=subsystem.replace("_", " ").title(),
            description=f"Selected component for the {subsystem.replace('_', ' ')} slot.",
            stock_part_id=part_id,
        )
        for subsystem, part_id in slot_map.items()
    )
    return VehicleBaseConfig(
        config_id=f"{trim_id}_imported_stock",
        trim_id=trim_id,
        subsystem_slots=subsystem_slots,
        stock_parts=[StockPartReference(subsystem=subsystem, stock_part_id=part_id) for subsystem, part_id in slot_map.items()],
        stock_configs=[StockConfigReference(subsystem="engine", stock_config_id=payload["defaults"]["engine_config_id"])],
    )


class CatalogSourceAdapter(ABC):
    adapter_mode: str

    @abstractmethod
    def fetch(self) -> list[RawSourceEnvelope]:
        raise NotImplementedError


class FixtureApiPullAdapter(CatalogSourceAdapter):
    adapter_mode = "api_pull"

    def fetch(self) -> list[RawSourceEnvelope]:
        fixture = _load_fixture_payload()
        observed_at = fixture["observed_at"]
        envelopes: list[RawSourceEnvelope] = []
        for entity_type in ("vehicles", "engine_families", "engine_configs", "drivetrain_configs", "parts"):
            for index, payload in enumerate(fixture.get(entity_type, []), start=1):
                envelopes.append(
                    RawSourceEnvelope(
                        entity_type=entity_type[:-1] if entity_type != "engine_families" else "engine_family",
                        source_id=FIXTURE_SOURCE_ID,
                        provider=FIXTURE_PROVIDER,
                        source_record_id=payload["record_id"],
                        observed_at=payload.get("observed_at", observed_at),
                        payload=payload,
                        metadata={"transport": "api_pull", "page": index},
                    )
                )
        return envelopes


class FixtureExportLoadAdapter(CatalogSourceAdapter):
    adapter_mode = "export_load"

    def fetch(self) -> list[RawSourceEnvelope]:
        fixture = _load_fixture_payload()
        observed_at = fixture["observed_at"]
        envelopes: list[RawSourceEnvelope] = []
        entity_map = {
            "vehicles": "vehicle",
            "engine_families": "engine_family",
            "engine_configs": "engine_config",
            "drivetrain_configs": "drivetrain_config",
            "parts": "part",
        }
        for entity_type, raw_type in entity_map.items():
            for payload in fixture.get(entity_type, []):
                envelopes.append(
                    RawSourceEnvelope(
                        entity_type=raw_type,
                        source_id=FIXTURE_SOURCE_ID,
                        provider=FIXTURE_PROVIDER,
                        source_record_id=payload["record_id"],
                        observed_at=payload.get("observed_at", observed_at),
                        payload=payload,
                        metadata={"transport": "export_load", "table": entity_type},
                    )
                )
        return envelopes


def _get_adapter(adapter_mode: str) -> CatalogSourceAdapter:
    if adapter_mode == "api_pull":
        return FixtureApiPullAdapter()
    return FixtureExportLoadAdapter()


def _normalize_vehicle(payload: dict[str, Any], import_run_id: str) -> CanonicalVehicleRecord:
    source_record_id = payload["record_id"]
    observed_at = payload.get("observed_at", _now_iso())
    vehicle = VehicleTrim.model_validate(
        {
            **payload["vehicle"],
            "provenance": _build_fact_provenance(source_record_id, observed_at, "normalized licensed vehicle trim"),
        }
    )
    platform = VehiclePlatform.model_validate(
        {
            **payload["platform"],
            "lineage": _build_lineage(f"platform:{payload['platform']['platform_id']}", import_run_id),
            "provenance": _build_fact_provenance(source_record_id, observed_at, "normalized licensed platform baseline"),
        }
    )
    chassis_envelope = ChassisEnvelope.model_validate(payload["chassis_envelope"])
    return CanonicalVehicleRecord(
        vehicle_id=vehicle.trim_id,
        label=f"{vehicle.year} {vehicle.make} {vehicle.model} {vehicle.trim}",
        vehicle=vehicle,
        platform=platform,
        chassis_envelope=chassis_envelope,
        base_config=_base_config_for_vehicle(vehicle.trim_id, payload),
        default_engine_config_id=payload["defaults"]["engine_config_id"],
        default_drivetrain_config_id=payload["defaults"]["drivetrain_config_id"],
        provenance=_record_provenance(
            source_record_id=source_record_id,
            import_run_id=import_run_id,
            observed_at=observed_at,
            summary=f"Imported vehicle record {source_record_id} from licensed fixture source.",
        ),
    )


def _normalize_engine_family(payload: dict[str, Any], import_run_id: str) -> CanonicalEngineFamilyRecord:
    source_record_id = payload["record_id"]
    observed_at = payload.get("observed_at", _now_iso())
    family = EngineFamily.model_validate(
        {
            **payload["engine_family"],
            "lineage": _build_lineage(source_record_id, import_run_id),
            "provenance": _build_fact_provenance(source_record_id, observed_at, "normalized licensed engine family"),
        }
    )
    return CanonicalEngineFamilyRecord(
        engine_family_id=family.engine_family_id,
        engine_family=family,
        provenance=_record_provenance(
            source_record_id=source_record_id,
            import_run_id=import_run_id,
            observed_at=observed_at,
            summary=f"Imported engine family {family.label} from licensed fixture source.",
        ),
    )


def _normalize_engine_config(payload: dict[str, Any], import_run_id: str) -> CanonicalEngineConfigRecord:
    source_record_id = payload["record_id"]
    observed_at = payload.get("observed_at", _now_iso())
    config = EngineBuildSpec.model_validate(
        {
            **payload["engine_config"],
            "valve_train": ValveTrainSpec.model_validate(payload["engine_config"]["valve_train"]),
            "cam_profile": CamProfileSpec.model_validate(payload["engine_config"]["cam_profile"]),
            "induction": InductionSpec.model_validate(payload["engine_config"]["induction"]),
            "fuel": FuelSpec.model_validate(payload["engine_config"]["fuel"]),
            "exhaust": ExhaustSpec.model_validate(payload["engine_config"]["exhaust"]),
        }
    )
    return CanonicalEngineConfigRecord(
        config_id=config.config_id,
        engine_config=config,
        provenance=_record_provenance(
            source_record_id=source_record_id,
            import_run_id=import_run_id,
            observed_at=observed_at,
            summary=f"Imported engine configuration {config.label} from licensed fixture source.",
        ),
    )


def _normalize_drivetrain_config(payload: dict[str, Any], import_run_id: str) -> CanonicalDrivetrainRecord:
    source_record_id = payload["record_id"]
    observed_at = payload.get("observed_at", _now_iso())
    config = DrivetrainConfig.model_validate(payload["drivetrain_config"])
    return CanonicalDrivetrainRecord(
        config_id=config.config_id,
        drivetrain_config=config,
        provenance=_record_provenance(
            source_record_id=source_record_id,
            import_run_id=import_run_id,
            observed_at=observed_at,
            summary=f"Imported drivetrain configuration {config.label} from licensed fixture source.",
        ),
    )


def _normalize_dependency_rules(
    rules: list[dict[str, Any]],
    *,
    source_record_id: str,
    observed_at: str,
) -> list[DependencyRule]:
    return [
        DependencyRule.model_validate(
            {
                **rule,
                "provenance": _build_fact_provenance(
                    source_record_id,
                    observed_at,
                    f"normalized dependency rule for {source_record_id}",
                ),
            }
        )
        for rule in rules
    ]


def _normalize_part(payload: dict[str, Any], import_run_id: str) -> CanonicalPartRecord:
    source_record_id = payload["record_id"]
    observed_at = payload.get("observed_at", _now_iso())
    part = PartCatalogItem.model_validate(
        {
            **payload["part"],
            "dependency_rules": _normalize_dependency_rules(
                payload["part"].get("dependency_rules", []),
                source_record_id=source_record_id,
                observed_at=observed_at,
            ),
            "lineage": _build_lineage(source_record_id, import_run_id),
            "provenance": _build_fact_provenance(source_record_id, observed_at, "normalized licensed part"),
        }
    )
    provenance = _record_provenance(
        source_record_id=source_record_id,
        import_run_id=import_run_id,
        observed_at=observed_at,
        summary=f"Imported part record {source_record_id} from licensed fixture source.",
    )
    applications = [
        CanonicalPartApplication(
            application_id=f"{part.part_id}:{fitment['vehicle_id']}",
            part_id=part.part_id,
            vehicle_id=fitment["vehicle_id"],
            fitment_status=fitment.get("fitment_status", "direct_fit"),
            required_mount_family=fitment.get("required_mount_family"),
            required_bellhousing_family=fitment.get("required_bellhousing_family"),
            required_bolt_pattern=fitment.get("required_bolt_pattern"),
            required_hub_bore_mm=fitment.get("required_hub_bore_mm"),
            minimum_wheel_diameter_in=fitment.get("minimum_wheel_diameter_in"),
            minimum_wheel_width_in=fitment.get("minimum_wheel_width_in"),
            minimum_tire_width_mm=fitment.get("minimum_tire_width_mm"),
            maximum_tire_width_mm=fitment.get("maximum_tire_width_mm"),
            required_drivetrain_family=fitment.get("required_drivetrain_family"),
            required_transmission_type=fitment.get("required_transmission_type"),
            required_ecu_family=fitment.get("required_ecu_family"),
            required_cooling_family=fitment.get("required_cooling_family"),
            required_supporting_part_ids=fitment.get("required_supporting_part_ids", []),
            excluded_part_ids=fitment.get("excluded_part_ids", []),
            notes=fitment.get("notes", []),
            provenance=provenance,
        )
        for fitment in payload.get("fitments", [])
    ]
    prices = [
        CanonicalPriceSnapshot(
            snapshot_id=price["snapshot_id"],
            part_id=part.part_id,
            source=price["source"],
            provider=FIXTURE_PROVIDER,
            source_id=FIXTURE_SOURCE_ID,
            source_record_id=source_record_id,
            import_run_id=import_run_id,
            price_usd=float(price["price_usd"]),
            currency=price.get("currency", "USD"),
            availability=price.get("availability", "unknown"),
            product_url=price.get("product_url"),
            observed_at=price.get("observed_at", observed_at),
            provenance_summary=price.get(
                "provenance_summary",
                f"Imported price snapshot for {part.part_id} from licensed fixture source.",
            ),
        )
        for price in payload.get("prices", [])
    ]
    asset = AssetCoverage.model_validate(
        {
            **payload["asset"],
            "proxy_geometry": payload["asset"].get("proxy_geometry"),
            "dimensions": payload["asset"].get("dimensions"),
        }
    )
    return CanonicalPartRecord(
        part_id=part.part_id,
        subsystem=part.subsystem,
        label=part.label,
        part=part,
        applications=applications,
        prices=prices,
        asset_coverage=asset,
        provenance=provenance,
    )


def _normalize_envelope(envelope: RawSourceEnvelope, import_run_id: str) -> tuple[str, Any]:
    if envelope.entity_type == "vehicle":
        return envelope.entity_type, _normalize_vehicle(envelope.payload, import_run_id)
    if envelope.entity_type == "engine_family":
        return envelope.entity_type, _normalize_engine_family(envelope.payload, import_run_id)
    if envelope.entity_type == "engine_config":
        return envelope.entity_type, _normalize_engine_config(envelope.payload, import_run_id)
    if envelope.entity_type == "drivetrain_config":
        return envelope.entity_type, _normalize_drivetrain_config(envelope.payload, import_run_id)
    if envelope.entity_type == "part":
        return envelope.entity_type, _normalize_part(envelope.payload, import_run_id)
    raise ValueError(f"Unsupported envelope type: {envelope.entity_type}")


def _persist_normalized(entity_type: str, record: Any) -> None:
    store = get_catalog_store()
    index = get_catalog_index()
    if entity_type == "vehicle":
        store.save_vehicle_record(record)
        index.index_vehicle(record)
        return
    if entity_type == "engine_family":
        store.save_engine_family_record(record)
        return
    if entity_type == "engine_config":
        store.save_engine_config_record(record)
        return
    if entity_type == "drivetrain_config":
        store.save_drivetrain_record(record)
        return
    if entity_type == "part":
        store.save_part_record(record)
        index.index_part(record)
        return
    raise ValueError(f"Unsupported normalized entity type: {entity_type}")


def _store_raw_payload(envelope: RawSourceEnvelope, run_id: str, attempt_id: str) -> None:
    payload_hash = _stable_hash(envelope.payload)
    get_catalog_store().save_raw_payload(
        RawSourcePayloadRecord(
            payload_id=f"raw_{payload_hash[:20]}",
            import_run_id=run_id,
            attempt_id=attempt_id,
            entity_type=envelope.entity_type,
            source_id=envelope.source_id,
            provider=envelope.provider,
            source_record_id=envelope.source_record_id,
            observed_at=envelope.observed_at,
            payload=envelope.payload,
            payload_hash=payload_hash,
            metadata=envelope.metadata,
        )
    )


def _hydrate_run_response(run: CatalogImportRun) -> CatalogImportRunResponse:
    store = get_catalog_store()
    raw_payloads = store.list_raw_payloads(run.import_run_id)
    attempts = store.list_import_attempts(run.import_run_id)
    entity_counts: dict[str, int] = {}
    for payload in raw_payloads:
        entity_counts[payload.entity_type] = entity_counts.get(payload.entity_type, 0) + 1
    return CatalogImportRunResponse(
        run=run,
        attempts=attempts,
        raw_payloads=len(raw_payloads),
        normalized_entities=entity_counts,
    )


def trigger_catalog_import(request: CatalogImportTriggerRequest) -> CatalogImportRunResponse:
    store = get_catalog_store()
    index = get_catalog_index()
    if request.force_reimport:
        store.clear_source(request.source_id)
        index.clear_source(request.source_id)

    existing_runs = [
        run
        for run in store.list_import_runs()
        if run.source_id == request.source_id and run.adapter_mode == request.adapter_mode and run.status == "succeeded"
    ]
    if existing_runs and not request.force_reimport:
        latest = sorted(existing_runs, key=lambda item: item.requested_at)[-1]
        return _hydrate_run_response(latest)

    run_id = f"import_{uuid4().hex[:12]}"
    attempt_id = f"attempt_{uuid4().hex[:12]}"
    run = CatalogImportRun(
        import_run_id=run_id,
        source_id=request.source_id,
        provider=FIXTURE_PROVIDER,
        adapter_mode=request.adapter_mode,
        status="running",
        requested_at=_now_iso(),
        started_at=_now_iso(),
        notes=list(DEFAULT_IMPORT_NOTES),
    )
    attempt = CatalogImportAttempt(
        attempt_id=attempt_id,
        import_run_id=run_id,
        adapter_mode=request.adapter_mode,
        status="running",
        started_at=_now_iso(),
    )
    store.save_import_run(run)
    store.save_import_attempt(attempt)

    adapter = _get_adapter(request.adapter_mode)
    envelopes = adapter.fetch()
    normalized_count = 0
    error_count = 0
    try:
        for envelope in envelopes:
            _store_raw_payload(envelope, run_id, attempt_id)
            entity_type, record = _normalize_envelope(envelope, run_id)
            _persist_normalized(entity_type, record)
            normalized_count += 1
        attempt = attempt.model_copy(update={"status": "succeeded", "completed_at": _now_iso()})
        run = run.model_copy(
            update={
                "status": "succeeded",
                "completed_at": _now_iso(),
                "raw_record_count": len(envelopes),
                "normalized_record_count": normalized_count,
            }
        )
    except Exception as exc:  # pragma: no cover - exercised through API contracts
        error_count += 1
        attempt = attempt.model_copy(
            update={"status": "failed", "completed_at": _now_iso(), "error_message": str(exc)}
        )
        run = run.model_copy(
            update={
                "status": "partial" if normalized_count else "failed",
                "completed_at": _now_iso(),
                "raw_record_count": len(envelopes),
                "normalized_record_count": normalized_count,
                "error_count": error_count,
                "notes": [*run.notes, str(exc)],
            }
        )
    store.save_import_attempt(attempt)
    store.save_import_run(run)
    return _hydrate_run_response(run)


def list_catalog_import_runs() -> list[CatalogImportRun]:
    return sorted(get_catalog_store().list_import_runs(), key=lambda item: item.requested_at, reverse=True)


def get_catalog_import_run(import_run_id: str) -> CatalogImportRunResponse | None:
    run = get_catalog_store().get_import_run(import_run_id)
    return None if run is None else _hydrate_run_response(run)


def retry_catalog_import(import_run_id: str) -> CatalogImportRunResponse | None:
    run = get_catalog_store().get_import_run(import_run_id)
    if run is None:
        return None
    return trigger_catalog_import(
        CatalogImportTriggerRequest(
            source_id=run.source_id,
            adapter_mode=run.adapter_mode,
            force_reimport=True,
        )
    )


def reindex_catalog_documents() -> dict[str, int]:
    index = get_catalog_index()
    store = get_catalog_store()
    index.clear_source(FIXTURE_SOURCE_ID)
    vehicle_count = 0
    for vehicle in store.list_vehicle_records():
        if vehicle.provenance.source_id != FIXTURE_SOURCE_ID:
            continue
        index.index_vehicle(vehicle)
        vehicle_count += 1
    part_count = 0
    for part in store.list_part_records():
        if part.provenance.source_id != FIXTURE_SOURCE_ID:
            continue
        index.index_part(part)
        part_count += 1
    return {"vehicles": vehicle_count, "parts": part_count}


def ensure_imported_slice() -> None:
    store = get_catalog_store()
    imported_vehicle_ids = [
        vehicle.vehicle_id
        for vehicle in store.list_vehicle_records()
        if vehicle.provenance.source_id == FIXTURE_SOURCE_ID
    ]
    if imported_vehicle_ids:
        reindex_catalog_documents()
        return
    trigger_catalog_import(CatalogImportTriggerRequest(source_id=FIXTURE_SOURCE_ID, adapter_mode="export_load"))


def import_seed_catalog(request: CatalogImportRequest) -> CatalogImportResponse:
    response = trigger_catalog_import(
        CatalogImportTriggerRequest(
            source_id=FIXTURE_SOURCE_ID,
            adapter_mode="export_load" if request.import_scope != "seed_engine_families" else "api_pull",
            force_reimport=request.import_scope == "seed_all",
        )
    )
    return CatalogImportResponse(
        import_batch=ImportBatch(
            import_batch_id=response.run.import_run_id,
            source_system=response.run.source_id,
            imported_at=response.run.completed_at or response.run.requested_at,
            status="complete" if response.run.status == "succeeded" else "pending",
            record_count=response.run.normalized_record_count,
            notes="Legacy seed import route now proxies to the imported catalog fixture slice.",
        ),
        imported_entities=response.normalized_entities,
        notes=response.run.notes,
    )
