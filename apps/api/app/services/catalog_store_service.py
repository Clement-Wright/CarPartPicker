from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from functools import lru_cache
from threading import Lock

from sqlalchemy import delete

from app.catalog_import_schemas import (
    CanonicalDrivetrainRecord,
    CanonicalEngineConfigRecord,
    CanonicalEngineFamilyRecord,
    CanonicalPartApplication,
    CanonicalPartRecord,
    CanonicalPriceSnapshot,
    CanonicalVehicleRecord,
    CatalogImportAttempt,
    CatalogImportRun,
    RawSourcePayloadRecord,
)
from app.db import (
    CatalogImportAttemptRecord,
    CatalogImportRunRecord,
    DigitalAssetRecord,
    DrivetrainConfigRecord,
    EngineConfigRecord,
    EngineFamilyRecord,
    PartApplicationRecord,
    PartRecord,
    PriceSnapshotRecord,
    RawSourcePayloadDbRecord,
    VehicleRecord,
    get_session_factory,
)


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _as_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


class CatalogStore(ABC):
    @abstractmethod
    def list_vehicle_records(self) -> list[CanonicalVehicleRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_vehicle_record(self, vehicle_id: str) -> CanonicalVehicleRecord | None:
        raise NotImplementedError

    @abstractmethod
    def save_vehicle_record(self, record: CanonicalVehicleRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_engine_family_records(self) -> list[CanonicalEngineFamilyRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_engine_family_record(self, engine_family_id: str) -> CanonicalEngineFamilyRecord | None:
        raise NotImplementedError

    @abstractmethod
    def save_engine_family_record(self, record: CanonicalEngineFamilyRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_engine_config_records(self) -> list[CanonicalEngineConfigRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_engine_config_record(self, config_id: str) -> CanonicalEngineConfigRecord | None:
        raise NotImplementedError

    @abstractmethod
    def save_engine_config_record(self, record: CanonicalEngineConfigRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_drivetrain_records(self) -> list[CanonicalDrivetrainRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_drivetrain_record(self, config_id: str) -> CanonicalDrivetrainRecord | None:
        raise NotImplementedError

    @abstractmethod
    def save_drivetrain_record(self, record: CanonicalDrivetrainRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_part_records(self) -> list[CanonicalPartRecord]:
        raise NotImplementedError

    @abstractmethod
    def get_part_record(self, part_id: str) -> CanonicalPartRecord | None:
        raise NotImplementedError

    @abstractmethod
    def save_part_record(self, record: CanonicalPartRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_part_applications(
        self,
        *,
        part_id: str | None = None,
        vehicle_id: str | None = None,
    ) -> list[CanonicalPartApplication]:
        raise NotImplementedError

    @abstractmethod
    def save_part_application(self, record: CanonicalPartApplication) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_price_snapshots(self, part_id: str | None = None) -> list[CanonicalPriceSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def save_price_snapshot(self, record: CanonicalPriceSnapshot) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_import_runs(self) -> list[CatalogImportRun]:
        raise NotImplementedError

    @abstractmethod
    def get_import_run(self, import_run_id: str) -> CatalogImportRun | None:
        raise NotImplementedError

    @abstractmethod
    def save_import_run(self, record: CatalogImportRun) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_import_attempts(self, import_run_id: str | None = None) -> list[CatalogImportAttempt]:
        raise NotImplementedError

    @abstractmethod
    def save_import_attempt(self, record: CatalogImportAttempt) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_raw_payloads(self, import_run_id: str | None = None) -> list[RawSourcePayloadRecord]:
        raise NotImplementedError

    @abstractmethod
    def save_raw_payload(self, record: RawSourcePayloadRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear_source(self, source_id: str) -> None:
        raise NotImplementedError


class InMemoryCatalogStore(CatalogStore):
    def __init__(self) -> None:
        self._lock = Lock()
        self._vehicles: dict[str, CanonicalVehicleRecord] = {}
        self._engine_families: dict[str, CanonicalEngineFamilyRecord] = {}
        self._engine_configs: dict[str, CanonicalEngineConfigRecord] = {}
        self._drivetrains: dict[str, CanonicalDrivetrainRecord] = {}
        self._parts: dict[str, CanonicalPartRecord] = {}
        self._applications: dict[str, CanonicalPartApplication] = {}
        self._prices: dict[str, CanonicalPriceSnapshot] = {}
        self._runs: dict[str, CatalogImportRun] = {}
        self._attempts: dict[str, CatalogImportAttempt] = {}
        self._raw_payloads: dict[str, RawSourcePayloadRecord] = {}

    def list_vehicle_records(self) -> list[CanonicalVehicleRecord]:
        return list(self._vehicles.values())

    def get_vehicle_record(self, vehicle_id: str) -> CanonicalVehicleRecord | None:
        return self._vehicles.get(vehicle_id)

    def save_vehicle_record(self, record: CanonicalVehicleRecord) -> None:
        with self._lock:
            self._vehicles[record.vehicle_id] = record

    def list_engine_family_records(self) -> list[CanonicalEngineFamilyRecord]:
        return list(self._engine_families.values())

    def get_engine_family_record(self, engine_family_id: str) -> CanonicalEngineFamilyRecord | None:
        return self._engine_families.get(engine_family_id)

    def save_engine_family_record(self, record: CanonicalEngineFamilyRecord) -> None:
        with self._lock:
            self._engine_families[record.engine_family_id] = record

    def list_engine_config_records(self) -> list[CanonicalEngineConfigRecord]:
        return list(self._engine_configs.values())

    def get_engine_config_record(self, config_id: str) -> CanonicalEngineConfigRecord | None:
        return self._engine_configs.get(config_id)

    def save_engine_config_record(self, record: CanonicalEngineConfigRecord) -> None:
        with self._lock:
            self._engine_configs[record.config_id] = record

    def list_drivetrain_records(self) -> list[CanonicalDrivetrainRecord]:
        return list(self._drivetrains.values())

    def get_drivetrain_record(self, config_id: str) -> CanonicalDrivetrainRecord | None:
        return self._drivetrains.get(config_id)

    def save_drivetrain_record(self, record: CanonicalDrivetrainRecord) -> None:
        with self._lock:
            self._drivetrains[record.config_id] = record

    def list_part_records(self) -> list[CanonicalPartRecord]:
        return list(self._parts.values())

    def get_part_record(self, part_id: str) -> CanonicalPartRecord | None:
        return self._parts.get(part_id)

    def save_part_record(self, record: CanonicalPartRecord) -> None:
        with self._lock:
            self._parts[record.part_id] = record
            for application in record.applications:
                self._applications[application.application_id] = application
            for price in record.prices:
                self._prices[price.snapshot_id] = price

    def list_part_applications(
        self,
        *,
        part_id: str | None = None,
        vehicle_id: str | None = None,
    ) -> list[CanonicalPartApplication]:
        items = list(self._applications.values())
        if part_id is not None:
            items = [item for item in items if item.part_id == part_id]
        if vehicle_id is not None:
            items = [item for item in items if item.vehicle_id == vehicle_id]
        return items

    def save_part_application(self, record: CanonicalPartApplication) -> None:
        with self._lock:
            self._applications[record.application_id] = record

    def list_price_snapshots(self, part_id: str | None = None) -> list[CanonicalPriceSnapshot]:
        items = list(self._prices.values())
        if part_id is not None:
            items = [item for item in items if item.part_id == part_id]
        return items

    def save_price_snapshot(self, record: CanonicalPriceSnapshot) -> None:
        with self._lock:
            self._prices[record.snapshot_id] = record

    def list_import_runs(self) -> list[CatalogImportRun]:
        return list(self._runs.values())

    def get_import_run(self, import_run_id: str) -> CatalogImportRun | None:
        return self._runs.get(import_run_id)

    def save_import_run(self, record: CatalogImportRun) -> None:
        with self._lock:
            self._runs[record.import_run_id] = record

    def list_import_attempts(self, import_run_id: str | None = None) -> list[CatalogImportAttempt]:
        items = list(self._attempts.values())
        if import_run_id is not None:
            items = [item for item in items if item.import_run_id == import_run_id]
        return items

    def save_import_attempt(self, record: CatalogImportAttempt) -> None:
        with self._lock:
            self._attempts[record.attempt_id] = record

    def list_raw_payloads(self, import_run_id: str | None = None) -> list[RawSourcePayloadRecord]:
        items = list(self._raw_payloads.values())
        if import_run_id is not None:
            items = [item for item in items if item.import_run_id == import_run_id]
        return items

    def save_raw_payload(self, record: RawSourcePayloadRecord) -> None:
        with self._lock:
            self._raw_payloads[record.payload_id] = record

    def clear_source(self, source_id: str) -> None:
        with self._lock:
            self._vehicles = {k: v for k, v in self._vehicles.items() if v.provenance.source_id != source_id}
            self._engine_families = {
                k: v for k, v in self._engine_families.items() if v.provenance.source_id != source_id
            }
            self._engine_configs = {
                k: v for k, v in self._engine_configs.items() if v.provenance.source_id != source_id
            }
            self._drivetrains = {k: v for k, v in self._drivetrains.items() if v.provenance.source_id != source_id}
            self._parts = {k: v for k, v in self._parts.items() if v.provenance.source_id != source_id}
            self._applications = {
                k: v for k, v in self._applications.items() if v.provenance.source_id != source_id
            }
            self._prices = {k: v for k, v in self._prices.items() if v.source_id != source_id}
            self._runs = {k: v for k, v in self._runs.items() if v.source_id != source_id}
            run_ids = {run_id for run_id in self._runs}
            self._attempts = {
                k: v for k, v in self._attempts.items() if v.import_run_id in run_ids or not run_ids
            }
            self._raw_payloads = {
                k: v for k, v in self._raw_payloads.items() if v.source_id != source_id
            }


class SqlCatalogStore(CatalogStore):
    def _session_factory(self):
        session_factory = get_session_factory()
        if session_factory is None:
            raise RuntimeError("Database session factory is not configured.")
        return session_factory

    def list_vehicle_records(self) -> list[CanonicalVehicleRecord]:
        with self._session_factory()() as session:
            return [CanonicalVehicleRecord.model_validate(item.vehicle_json) for item in session.query(VehicleRecord).all()]

    def get_vehicle_record(self, vehicle_id: str) -> CanonicalVehicleRecord | None:
        with self._session_factory()() as session:
            record = session.get(VehicleRecord, vehicle_id)
            return None if record is None else CanonicalVehicleRecord.model_validate(record.vehicle_json)

    def save_vehicle_record(self, record: CanonicalVehicleRecord) -> None:
        payload = record.model_dump(mode="json")
        with self._session_factory()() as session:
            db_record = session.get(VehicleRecord, record.vehicle_id)
            if db_record is None:
                db_record = VehicleRecord(
                    vehicle_id=record.vehicle_id,
                    label=record.label,
                    vehicle_json=payload,
                )
                session.add(db_record)
            db_record.source_id = record.provenance.source_id
            db_record.provider = record.provenance.provider
            db_record.source_record_id = record.provenance.source_record_id
            db_record.import_run_id = record.provenance.import_run_id
            db_record.verification_status = record.provenance.verification_status
            db_record.supported_slice = True
            db_record.source_mode = record.source_mode
            db_record.label = record.label
            db_record.vehicle_json = payload
            db_record.updated_at = datetime.utcnow()
            session.commit()

    def list_engine_family_records(self) -> list[CanonicalEngineFamilyRecord]:
        with self._session_factory()() as session:
            return [
                CanonicalEngineFamilyRecord.model_validate(item.engine_family_json)
                for item in session.query(EngineFamilyRecord).all()
            ]

    def get_engine_family_record(self, engine_family_id: str) -> CanonicalEngineFamilyRecord | None:
        with self._session_factory()() as session:
            record = session.get(EngineFamilyRecord, engine_family_id)
            return None if record is None else CanonicalEngineFamilyRecord.model_validate(record.engine_family_json)

    def save_engine_family_record(self, record: CanonicalEngineFamilyRecord) -> None:
        payload = record.model_dump(mode="json")
        with self._session_factory()() as session:
            db_record = session.get(EngineFamilyRecord, record.engine_family_id)
            if db_record is None:
                db_record = EngineFamilyRecord(
                    engine_family_id=record.engine_family_id,
                    label=record.engine_family.label,
                    engine_family_json=payload,
                )
                session.add(db_record)
            db_record.source_id = record.provenance.source_id
            db_record.provider = record.provenance.provider
            db_record.source_record_id = record.provenance.source_record_id
            db_record.import_run_id = record.provenance.import_run_id
            db_record.verification_status = record.provenance.verification_status
            db_record.source_mode = record.source_mode
            db_record.label = record.engine_family.label
            db_record.engine_family_json = payload
            db_record.updated_at = datetime.utcnow()
            session.commit()

    def list_engine_config_records(self) -> list[CanonicalEngineConfigRecord]:
        with self._session_factory()() as session:
            return [
                CanonicalEngineConfigRecord.model_validate(item.engine_config_json)
                for item in session.query(EngineConfigRecord).all()
            ]

    def get_engine_config_record(self, config_id: str) -> CanonicalEngineConfigRecord | None:
        with self._session_factory()() as session:
            record = session.get(EngineConfigRecord, config_id)
            return None if record is None else CanonicalEngineConfigRecord.model_validate(record.engine_config_json)

    def save_engine_config_record(self, record: CanonicalEngineConfigRecord) -> None:
        payload = record.model_dump(mode="json")
        with self._session_factory()() as session:
            db_record = session.get(EngineConfigRecord, record.config_id)
            if db_record is None:
                db_record = EngineConfigRecord(
                    config_id=record.config_id,
                    engine_family_id=record.engine_config.engine_family_id,
                    label=record.engine_config.label,
                    engine_config_json=payload,
                )
                session.add(db_record)
            db_record.engine_family_id = record.engine_config.engine_family_id
            db_record.source_id = record.provenance.source_id
            db_record.provider = record.provenance.provider
            db_record.source_record_id = record.provenance.source_record_id
            db_record.import_run_id = record.provenance.import_run_id
            db_record.verification_status = record.provenance.verification_status
            db_record.source_mode = record.source_mode
            db_record.label = record.engine_config.label
            db_record.engine_config_json = payload
            db_record.updated_at = datetime.utcnow()
            session.commit()

    def list_drivetrain_records(self) -> list[CanonicalDrivetrainRecord]:
        with self._session_factory()() as session:
            return [
                CanonicalDrivetrainRecord.model_validate(item.drivetrain_config_json)
                for item in session.query(DrivetrainConfigRecord).all()
            ]

    def get_drivetrain_record(self, config_id: str) -> CanonicalDrivetrainRecord | None:
        with self._session_factory()() as session:
            record = session.get(DrivetrainConfigRecord, config_id)
            return None if record is None else CanonicalDrivetrainRecord.model_validate(record.drivetrain_config_json)

    def save_drivetrain_record(self, record: CanonicalDrivetrainRecord) -> None:
        payload = record.model_dump(mode="json")
        with self._session_factory()() as session:
            db_record = session.get(DrivetrainConfigRecord, record.config_id)
            if db_record is None:
                db_record = DrivetrainConfigRecord(
                    config_id=record.config_id,
                    label=record.drivetrain_config.label,
                    drivetrain_config_json=payload,
                )
                session.add(db_record)
            db_record.source_id = record.provenance.source_id
            db_record.provider = record.provenance.provider
            db_record.source_record_id = record.provenance.source_record_id
            db_record.import_run_id = record.provenance.import_run_id
            db_record.verification_status = record.provenance.verification_status
            db_record.source_mode = record.source_mode
            db_record.label = record.drivetrain_config.label
            db_record.drivetrain_config_json = payload
            db_record.updated_at = datetime.utcnow()
            session.commit()

    def list_part_records(self) -> list[CanonicalPartRecord]:
        with self._session_factory()() as session:
            return [CanonicalPartRecord.model_validate(item.part_json) for item in session.query(PartRecord).all()]

    def get_part_record(self, part_id: str) -> CanonicalPartRecord | None:
        with self._session_factory()() as session:
            record = session.get(PartRecord, part_id)
            return None if record is None else CanonicalPartRecord.model_validate(record.part_json)

    def save_part_record(self, record: CanonicalPartRecord) -> None:
        payload = record.model_dump(mode="json")
        with self._session_factory()() as session:
            db_record = session.get(PartRecord, record.part_id)
            if db_record is None:
                db_record = PartRecord(
                    part_id=record.part_id,
                    subsystem=record.subsystem,
                    brand=record.part.brand,
                    label=record.label,
                    part_json=payload,
                )
                session.add(db_record)
            db_record.subsystem = record.subsystem
            db_record.brand = record.part.brand
            db_record.label = record.label
            db_record.source_id = record.provenance.source_id
            db_record.provider = record.provenance.provider
            db_record.source_record_id = record.provenance.source_record_id
            db_record.import_run_id = record.provenance.import_run_id
            db_record.verification_status = record.provenance.verification_status
            db_record.supported_slice = record.supported_slice
            db_record.source_mode = record.source_mode
            db_record.part_json = payload
            db_record.updated_at = datetime.utcnow()

            session.execute(delete(PartApplicationRecord).where(PartApplicationRecord.part_id == record.part_id))
            session.execute(delete(PriceSnapshotRecord).where(PriceSnapshotRecord.part_id == record.part_id))
            session.execute(delete(DigitalAssetRecord).where(DigitalAssetRecord.part_id == record.part_id))

            for application in record.applications:
                session.add(
                    PartApplicationRecord(
                        part_id=application.part_id,
                        vehicle_id=application.vehicle_id,
                        source_id=application.provenance.source_id,
                        provider=application.provenance.provider,
                        source_record_id=application.provenance.source_record_id,
                        import_run_id=application.provenance.import_run_id,
                        application_json=application.model_dump(mode="json"),
                    )
                )
            for price in record.prices:
                session.add(
                    PriceSnapshotRecord(
                        part_id=price.part_id,
                        source=price.source,
                        provider=price.provider,
                        source_id=price.source_id,
                        source_record_id=price.source_record_id,
                        import_run_id=price.import_run_id,
                        source_mode=price.source_mode,
                        price_usd=price.price_usd,
                        currency=price.currency,
                        availability=price.availability,
                        metadata_json=price.model_dump(mode="json"),
                        observed_at=_parse_dt(price.observed_at) or datetime.utcnow(),
                    )
                )
            session.add(
                DigitalAssetRecord(
                    asset_id=f"asset_{record.part_id}",
                    part_id=record.part_id,
                    asset_type="scene_policy",
                    readiness_status=record.asset_coverage.visualization_mode,
                    source_id=record.provenance.source_id,
                    provider=record.provenance.provider,
                    source_record_id=record.provenance.source_record_id,
                    import_run_id=record.provenance.import_run_id,
                    storage_uri=record.asset_coverage.mesh_url,
                    asset_json=record.asset_coverage.model_dump(mode="json"),
                )
            )
            session.commit()

    def list_part_applications(
        self,
        *,
        part_id: str | None = None,
        vehicle_id: str | None = None,
    ) -> list[CanonicalPartApplication]:
        with self._session_factory()() as session:
            query = session.query(PartApplicationRecord)
            if part_id is not None:
                query = query.filter(PartApplicationRecord.part_id == part_id)
            if vehicle_id is not None:
                query = query.filter(PartApplicationRecord.vehicle_id == vehicle_id)
            return [CanonicalPartApplication.model_validate(item.application_json) for item in query.all()]

    def save_part_application(self, record: CanonicalPartApplication) -> None:
        with self._session_factory()() as session:
            session.add(
                PartApplicationRecord(
                    part_id=record.part_id,
                    vehicle_id=record.vehicle_id,
                    source_id=record.provenance.source_id,
                    provider=record.provenance.provider,
                    source_record_id=record.provenance.source_record_id,
                    import_run_id=record.provenance.import_run_id,
                    application_json=record.model_dump(mode="json"),
                )
            )
            session.commit()

    def list_price_snapshots(self, part_id: str | None = None) -> list[CanonicalPriceSnapshot]:
        with self._session_factory()() as session:
            query = session.query(PriceSnapshotRecord)
            if part_id is not None:
                query = query.filter(PriceSnapshotRecord.part_id == part_id)
            return [CanonicalPriceSnapshot.model_validate(item.metadata_json) for item in query.all()]

    def save_price_snapshot(self, record: CanonicalPriceSnapshot) -> None:
        with self._session_factory()() as session:
            session.add(
                PriceSnapshotRecord(
                    part_id=record.part_id,
                    source=record.source,
                    provider=record.provider,
                    source_id=record.source_id,
                    source_record_id=record.source_record_id,
                    import_run_id=record.import_run_id,
                    source_mode=record.source_mode,
                    price_usd=record.price_usd,
                    currency=record.currency,
                    availability=record.availability,
                    metadata_json=record.model_dump(mode="json"),
                    observed_at=_parse_dt(record.observed_at) or datetime.utcnow(),
                )
            )
            session.commit()

    def list_import_runs(self) -> list[CatalogImportRun]:
        with self._session_factory()() as session:
            return [
                CatalogImportRun(
                    import_run_id=item.import_run_id,
                    source_id=item.source_id,
                    provider=item.provider,
                    adapter_mode=item.adapter_mode,
                    status=item.status,
                    categories=item.categories_json,
                    requested_at=_as_iso(item.requested_at) or "",
                    started_at=_as_iso(item.started_at),
                    completed_at=_as_iso(item.completed_at),
                    raw_record_count=item.raw_record_count,
                    normalized_record_count=item.normalized_record_count,
                    error_count=item.error_count,
                    notes=item.notes_json,
                    metadata=item.metadata_json,
                )
                for item in session.query(CatalogImportRunRecord).all()
            ]

    def get_import_run(self, import_run_id: str) -> CatalogImportRun | None:
        with self._session_factory()() as session:
            item = session.get(CatalogImportRunRecord, import_run_id)
            if item is None:
                return None
            return CatalogImportRun(
                import_run_id=item.import_run_id,
                source_id=item.source_id,
                provider=item.provider,
                adapter_mode=item.adapter_mode,
                status=item.status,
                categories=item.categories_json,
                requested_at=_as_iso(item.requested_at) or "",
                started_at=_as_iso(item.started_at),
                completed_at=_as_iso(item.completed_at),
                raw_record_count=item.raw_record_count,
                normalized_record_count=item.normalized_record_count,
                error_count=item.error_count,
                notes=item.notes_json,
                metadata=item.metadata_json,
            )

    def save_import_run(self, record: CatalogImportRun) -> None:
        with self._session_factory()() as session:
            db_record = session.get(CatalogImportRunRecord, record.import_run_id)
            if db_record is None:
                db_record = CatalogImportRunRecord(
                    import_run_id=record.import_run_id,
                    source_id=record.source_id,
                    provider=record.provider,
                    adapter_mode=record.adapter_mode,
                )
                session.add(db_record)
            db_record.source_id = record.source_id
            db_record.provider = record.provider
            db_record.adapter_mode = record.adapter_mode
            db_record.status = record.status
            db_record.categories_json = record.categories
            db_record.requested_at = _parse_dt(record.requested_at) or datetime.utcnow()
            db_record.started_at = _parse_dt(record.started_at)
            db_record.completed_at = _parse_dt(record.completed_at)
            db_record.raw_record_count = record.raw_record_count
            db_record.normalized_record_count = record.normalized_record_count
            db_record.error_count = record.error_count
            db_record.notes_json = record.notes
            db_record.metadata_json = record.metadata
            session.commit()

    def list_import_attempts(self, import_run_id: str | None = None) -> list[CatalogImportAttempt]:
        with self._session_factory()() as session:
            query = session.query(CatalogImportAttemptRecord)
            if import_run_id is not None:
                query = query.filter(CatalogImportAttemptRecord.import_run_id == import_run_id)
            return [
                CatalogImportAttempt(
                    attempt_id=item.attempt_id,
                    import_run_id=item.import_run_id,
                    adapter_mode=item.adapter_mode,
                    status=item.status,
                    started_at=_as_iso(item.started_at) or "",
                    completed_at=_as_iso(item.completed_at),
                    error_message=item.error_message,
                    metadata=item.metadata_json,
                )
                for item in query.all()
            ]

    def save_import_attempt(self, record: CatalogImportAttempt) -> None:
        with self._session_factory()() as session:
            db_record = session.get(CatalogImportAttemptRecord, record.attempt_id)
            if db_record is None:
                db_record = CatalogImportAttemptRecord(
                    attempt_id=record.attempt_id,
                    import_run_id=record.import_run_id,
                    adapter_mode=record.adapter_mode,
                )
                session.add(db_record)
            db_record.import_run_id = record.import_run_id
            db_record.adapter_mode = record.adapter_mode
            db_record.status = record.status
            db_record.started_at = _parse_dt(record.started_at) or datetime.utcnow()
            db_record.completed_at = _parse_dt(record.completed_at)
            db_record.error_message = record.error_message
            db_record.metadata_json = record.metadata
            session.commit()

    def list_raw_payloads(self, import_run_id: str | None = None) -> list[RawSourcePayloadRecord]:
        with self._session_factory()() as session:
            query = session.query(RawSourcePayloadDbRecord)
            if import_run_id is not None:
                query = query.filter(RawSourcePayloadDbRecord.import_run_id == import_run_id)
            return [
                RawSourcePayloadRecord(
                    payload_id=item.payload_id,
                    import_run_id=item.import_run_id,
                    attempt_id=item.attempt_id,
                    entity_type=item.entity_type,
                    source_id=item.source_id,
                    provider=item.provider,
                    source_record_id=item.source_record_id,
                    observed_at=_as_iso(item.observed_at) or "",
                    payload=item.payload_json,
                    payload_hash=item.payload_hash,
                    metadata=item.metadata_json,
                )
                for item in query.all()
            ]

    def save_raw_payload(self, record: RawSourcePayloadRecord) -> None:
        with self._session_factory()() as session:
            db_record = session.get(RawSourcePayloadDbRecord, record.payload_id)
            if db_record is None:
                db_record = RawSourcePayloadDbRecord(
                    payload_id=record.payload_id,
                    import_run_id=record.import_run_id,
                    attempt_id=record.attempt_id,
                    entity_type=record.entity_type,
                    source_id=record.source_id,
                    provider=record.provider,
                    source_record_id=record.source_record_id,
                    payload_hash=record.payload_hash,
                    payload_json=record.payload,
                )
                session.add(db_record)
            db_record.import_run_id = record.import_run_id
            db_record.attempt_id = record.attempt_id
            db_record.entity_type = record.entity_type
            db_record.source_id = record.source_id
            db_record.provider = record.provider
            db_record.source_record_id = record.source_record_id
            db_record.observed_at = _parse_dt(record.observed_at) or datetime.utcnow()
            db_record.payload_hash = record.payload_hash
            db_record.payload_json = record.payload
            db_record.metadata_json = record.metadata
            session.commit()

    def clear_source(self, source_id: str) -> None:
        with self._session_factory()() as session:
            session.execute(delete(PriceSnapshotRecord).where(PriceSnapshotRecord.source_id == source_id))
            session.execute(delete(DigitalAssetRecord).where(DigitalAssetRecord.source_id == source_id))
            session.execute(delete(PartApplicationRecord).where(PartApplicationRecord.source_id == source_id))
            session.execute(delete(PartRecord).where(PartRecord.source_id == source_id))
            session.execute(delete(DrivetrainConfigRecord).where(DrivetrainConfigRecord.source_id == source_id))
            session.execute(delete(EngineConfigRecord).where(EngineConfigRecord.source_id == source_id))
            session.execute(delete(EngineFamilyRecord).where(EngineFamilyRecord.source_id == source_id))
            session.execute(delete(VehicleRecord).where(VehicleRecord.source_id == source_id))
            session.execute(delete(RawSourcePayloadDbRecord).where(RawSourcePayloadDbRecord.source_id == source_id))
            run_ids = [
                item.import_run_id
                for item in session.query(CatalogImportRunRecord.import_run_id)
                .filter(CatalogImportRunRecord.source_id == source_id)
                .all()
            ]
            if run_ids:
                session.execute(delete(CatalogImportAttemptRecord).where(CatalogImportAttemptRecord.import_run_id.in_(run_ids)))
                session.execute(delete(CatalogImportRunRecord).where(CatalogImportRunRecord.import_run_id.in_(run_ids)))
            session.commit()


@lru_cache
def get_catalog_store() -> CatalogStore:
    if get_session_factory() is not None:
        return SqlCatalogStore()
    return InMemoryCatalogStore()


def reset_catalog_store() -> None:
    store = get_catalog_store()
    if isinstance(store, InMemoryCatalogStore):
        store.clear_source("licensed_fixture_catalog")
