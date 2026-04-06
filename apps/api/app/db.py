from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class TrimRecord(Base):
    __tablename__ = "trims"

    trim_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    platform: Mapped[str] = mapped_column(String(32))
    year: Mapped[int] = mapped_column(Integer)
    make: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(64))
    trim: Mapped[str] = mapped_column(String(64))
    stock_wheel_diameter: Mapped[int] = mapped_column(Integer)
    safety_index: Mapped[float] = mapped_column(Float)
    mod_potential: Mapped[float] = mapped_column(Float)


class NhtsaSnapshotRecord(Base):
    __tablename__ = "nhtsa_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trim_id: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RecommendationCacheRecord(Base):
    __tablename__ = "recommendation_cache"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class IngestAuditRecord(Base):
    __tablename__ = "ingest_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dataset: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32))
    detail: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CatalogSourceRecord(Base):
    __tablename__ = "catalog_sources"

    source_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    provider: Mapped[str] = mapped_column(String(128))
    contract_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="planned")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CatalogImportRunRecord(Base):
    __tablename__ = "catalog_import_runs"

    import_run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(128))
    adapter_mode: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    categories_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    raw_record_count: Mapped[int] = mapped_column(Integer, default=0)
    normalized_record_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    notes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class CatalogImportAttemptRecord(Base):
    __tablename__ = "catalog_import_attempts"

    attempt_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_run_id: Mapped[str] = mapped_column(String(64), index=True)
    adapter_mode: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class RawSourcePayloadDbRecord(Base):
    __tablename__ = "raw_source_payloads"

    payload_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_run_id: Mapped[str] = mapped_column(String(64), index=True)
    attempt_id: Mapped[str] = mapped_column(String(64), index=True)
    entity_type: Mapped[str] = mapped_column(String(32), index=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(128))
    source_record_id: Mapped[str] = mapped_column(String(128), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    payload_hash: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VehicleRecord(Base):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True, default="seed_catalog")
    provider: Mapped[str] = mapped_column(String(128), default="seed_catalog")
    source_record_id: Mapped[str] = mapped_column(String(128), default="")
    import_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="seeded")
    supported_slice: Mapped[bool] = mapped_column(Boolean, default=False)
    source_mode: Mapped[str] = mapped_column(String(32), default="seed")
    label: Mapped[str] = mapped_column(String(255))
    vehicle_json: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EngineFamilyRecord(Base):
    __tablename__ = "engine_families"

    engine_family_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True, default="seed_catalog")
    provider: Mapped[str] = mapped_column(String(128), default="seed_catalog")
    source_record_id: Mapped[str] = mapped_column(String(128), default="")
    import_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="seeded")
    source_mode: Mapped[str] = mapped_column(String(32), default="seed")
    label: Mapped[str] = mapped_column(String(255))
    engine_family_json: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EngineConfigRecord(Base):
    __tablename__ = "engine_configs"

    config_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    engine_family_id: Mapped[str] = mapped_column(String(64), index=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True, default="seed_catalog")
    provider: Mapped[str] = mapped_column(String(128), default="seed_catalog")
    source_record_id: Mapped[str] = mapped_column(String(128), default="")
    import_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="seeded")
    source_mode: Mapped[str] = mapped_column(String(32), default="seed")
    label: Mapped[str] = mapped_column(String(255))
    engine_config_json: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DrivetrainConfigRecord(Base):
    __tablename__ = "drivetrain_configs"

    config_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True, default="seed_catalog")
    provider: Mapped[str] = mapped_column(String(128), default="seed_catalog")
    source_record_id: Mapped[str] = mapped_column(String(128), default="")
    import_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="seeded")
    source_mode: Mapped[str] = mapped_column(String(32), default="seed")
    label: Mapped[str] = mapped_column(String(255))
    drivetrain_config_json: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PartRecord(Base):
    __tablename__ = "parts"

    part_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    subsystem: Mapped[str] = mapped_column(String(64), index=True)
    brand: Mapped[str] = mapped_column(String(128))
    label: Mapped[str] = mapped_column(String(255))
    source_id: Mapped[str] = mapped_column(String(64), index=True, default="seed_catalog")
    provider: Mapped[str] = mapped_column(String(128), default="seed_catalog")
    source_record_id: Mapped[str] = mapped_column(String(128), default="")
    import_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="seeded")
    supported_slice: Mapped[bool] = mapped_column(Boolean, default=False)
    source_mode: Mapped[str] = mapped_column(String(32), default="seed")
    part_json: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PartApplicationRecord(Base):
    __tablename__ = "part_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_id: Mapped[str] = mapped_column(String(64), index=True)
    vehicle_id: Mapped[str] = mapped_column(String(64), index=True)
    source_id: Mapped[str] = mapped_column(String(64), index=True, default="seed_catalog")
    provider: Mapped[str] = mapped_column(String(128), default="seed_catalog")
    source_record_id: Mapped[str] = mapped_column(String(128), default="")
    import_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    application_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DigitalAssetRecord(Base):
    __tablename__ = "digital_assets"

    asset_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    part_id: Mapped[str] = mapped_column(String(64), index=True)
    asset_type: Mapped[str] = mapped_column(String(64))
    readiness_status: Mapped[str] = mapped_column(String(32), default="missing_exact_asset")
    source_id: Mapped[str] = mapped_column(String(64), index=True, default="seed_catalog")
    provider: Mapped[str] = mapped_column(String(128), default="seed_catalog")
    source_record_id: Mapped[str] = mapped_column(String(128), default="")
    import_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    storage_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    asset_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PriceSnapshotRecord(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    part_id: Mapped[str] = mapped_column(String(64), index=True)
    source: Mapped[str] = mapped_column(String(128))
    provider: Mapped[str] = mapped_column(String(128), default="seed_catalog")
    source_id: Mapped[str] = mapped_column(String(64), index=True, default="seed_catalog")
    source_record_id: Mapped[str] = mapped_column(String(128), default="")
    import_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    source_mode: Mapped[str] = mapped_column(String(32), default="seed")
    price_usd: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    availability: Mapped[str] = mapped_column(String(64), default="unknown")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    observed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BuildStateRecord(Base):
    __tablename__ = "build_states"

    build_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    build_hash: Mapped[str] = mapped_column(String(32), index=True)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    source_mode: Mapped[str] = mapped_column(String(32), default="seed")
    build_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


@lru_cache
def get_engine() -> Engine | None:
    settings = get_settings()
    if not settings.postgres_url:
        return None
    return create_engine(settings.postgres_url, future=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session] | None:
    engine = get_engine()
    if engine is None:
        return None
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    engine = get_engine()
    if engine is None:
        return
    Base.metadata.create_all(engine)
