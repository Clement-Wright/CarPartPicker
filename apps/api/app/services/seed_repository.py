from __future__ import annotations

from functools import lru_cache

from app.catalog_import_schemas import CanonicalPartRecord, CanonicalPriceSnapshot, SUPPORTED_IMPORTED_PART_SUBSYSTEMS
from app.schemas import (
    BuildPreset,
    ChassisEnvelope,
    DecodedVehicle,
    DrivetrainConfig,
    EngineBuildSpec,
    EngineFamily,
    ImportBatch,
    PartCatalogItem,
    ScenarioDefinition,
    VehicleBaseConfig,
    VehiclePlatform,
    VehicleTrim,
)
from app.services.catalog_ingest_service import ensure_imported_slice
from app.services.catalog_seed import (
    BASE_CONFIGS,
    CHASSIS_ENVELOPES,
    DEFAULT_DRIVETRAIN_BY_TRIM,
    DEFAULT_ENGINE_BY_TRIM,
    DRIVETRAIN_CONFIGS,
    ENGINE_CONFIGS,
    ENGINE_FAMILIES,
    IMPORT_BATCHES,
    PARTS,
    PLATFORMS,
    PRESETS,
    SCENARIO_DEFINITIONS,
    TRIMS,
    VIN_CACHE,
)
from app.services.catalog_store_service import get_catalog_store


class SeedCatalogRepository:
    def list_trims(self) -> list[VehicleTrim]:
        return sorted(TRIMS.values(), key=lambda trim: (trim.year, trim.make, trim.model, trim.trim))

    def get_trim(self, trim_id: str) -> VehicleTrim:
        return TRIMS[trim_id]

    def get_platform(self, platform_id: str) -> VehiclePlatform:
        return PLATFORMS[platform_id]

    def get_chassis_envelope(self, platform_id: str) -> ChassisEnvelope:
        return CHASSIS_ENVELOPES[platform_id]

    def get_base_config(self, trim_id: str) -> VehicleBaseConfig:
        return BASE_CONFIGS[trim_id]

    def list_parts(self) -> list[PartCatalogItem]:
        return list(PARTS.values())

    def get_part(self, part_id: str) -> PartCatalogItem:
        return PARTS[part_id]

    def get_preset(self, preset_id: str) -> BuildPreset:
        return PRESETS[preset_id]

    def list_presets(self) -> list[BuildPreset]:
        return list(PRESETS.values())

    def list_scenarios(self) -> list[ScenarioDefinition]:
        return list(SCENARIO_DEFINITIONS.values())

    def get_scenario(self, scenario_name: str) -> ScenarioDefinition:
        return SCENARIO_DEFINITIONS[scenario_name]

    def list_engine_families(self) -> list[EngineFamily]:
        return list(ENGINE_FAMILIES.values())

    def get_engine_family(self, engine_family_id: str) -> EngineFamily:
        return ENGINE_FAMILIES[engine_family_id]

    def get_default_engine_config(self, trim_id: str) -> EngineBuildSpec:
        return ENGINE_CONFIGS[DEFAULT_ENGINE_BY_TRIM[trim_id]]

    def get_engine_config(self, config_id: str) -> EngineBuildSpec:
        return ENGINE_CONFIGS[config_id]

    def list_drivetrain_configs(self) -> list[DrivetrainConfig]:
        return list(DRIVETRAIN_CONFIGS.values())

    def get_default_drivetrain_config(self, trim_id: str) -> DrivetrainConfig:
        return DRIVETRAIN_CONFIGS[DEFAULT_DRIVETRAIN_BY_TRIM[trim_id]]

    def get_drivetrain_config(self, config_id: str) -> DrivetrainConfig:
        return DRIVETRAIN_CONFIGS[config_id]

    def list_import_batches(self) -> list[ImportBatch]:
        return list(IMPORT_BATCHES.values())

    def lookup_vin(self, vin: str) -> DecodedVehicle | None:
        payload = VIN_CACHE.get(vin.upper())
        if not payload:
            return None
        return DecodedVehicle(vin=vin.upper(), source="seed_cache", cache_hit=True, **payload)

    def find_trim_by_vehicle(
        self,
        *,
        year: int | None,
        make: str | None,
        model: str | None,
        trim: str | None = None,
    ) -> VehicleTrim | None:
        candidates = [
            item
            for item in TRIMS.values()
            if (year is None or item.year == year)
            and (make is None or item.make.lower() == make.lower())
            and (model is None or item.model.lower() == model.lower())
        ]
        if trim:
            for candidate in candidates:
                if candidate.trim.lower() == trim.lower():
                    return candidate
        return candidates[0] if candidates else None


class CatalogRepository:
    def __init__(self) -> None:
        ensure_imported_slice()
        self._seed = SeedCatalogRepository()
        self._store = get_catalog_store()

    def _imported_vehicles(self) -> dict[str, VehicleTrim]:
        return {
            record.vehicle_id: record.vehicle
            for record in self._store.list_vehicle_records()
            if record.provenance.source_id == "licensed_fixture_catalog"
        }

    def _imported_platforms(self) -> dict[str, VehiclePlatform]:
        return {
            record.platform.platform_id: record.platform
            for record in self._store.list_vehicle_records()
            if record.provenance.source_id == "licensed_fixture_catalog"
        }

    def _imported_chassis(self) -> dict[str, ChassisEnvelope]:
        return {
            record.chassis_envelope.platform_id: record.chassis_envelope
            for record in self._store.list_vehicle_records()
            if record.provenance.source_id == "licensed_fixture_catalog"
        }

    def _vehicle_record(self, trim_id: str):
        return self._store.get_vehicle_record(trim_id)

    def _part_record(self, part_id: str) -> CanonicalPartRecord | None:
        return self._store.get_part_record(part_id)

    def _seed_fallback_allowed(self, subsystem: str) -> bool:
        return subsystem not in SUPPORTED_IMPORTED_PART_SUBSYSTEMS

    def list_trims(self) -> list[VehicleTrim]:
        imported = list(self._imported_vehicles().values())
        if imported:
            return sorted(imported, key=lambda trim: (trim.year, trim.make, trim.model, trim.trim))
        return self._seed.list_trims()

    def get_trim(self, trim_id: str) -> VehicleTrim:
        record = self._vehicle_record(trim_id)
        if record is not None:
            return record.vehicle
        if self._imported_vehicles():
            raise KeyError(trim_id)
        return self._seed.get_trim(trim_id)

    def get_vehicle_record(self, trim_id: str):
        return self._vehicle_record(trim_id)

    def get_platform(self, platform_id: str) -> VehiclePlatform:
        platform = self._imported_platforms().get(platform_id)
        if platform is not None:
            return platform
        if self._imported_platforms():
            raise KeyError(platform_id)
        return self._seed.get_platform(platform_id)

    def get_chassis_envelope(self, platform_id: str) -> ChassisEnvelope:
        envelope = self._imported_chassis().get(platform_id)
        if envelope is not None:
            return envelope
        if self._imported_chassis():
            raise KeyError(platform_id)
        return self._seed.get_chassis_envelope(platform_id)

    def get_base_config(self, trim_id: str) -> VehicleBaseConfig:
        record = self._vehicle_record(trim_id)
        if record is not None:
            return record.base_config
        if self._imported_vehicles():
            raise KeyError(trim_id)
        return self._seed.get_base_config(trim_id)

    def list_parts(self) -> list[PartCatalogItem]:
        imported = {
            record.part_id: record.part
            for record in self._store.list_part_records()
            if record.provenance.source_id == "licensed_fixture_catalog"
        }
        seed_parts = [
            part
            for part in self._seed.list_parts()
            if part.subsystem not in SUPPORTED_IMPORTED_PART_SUBSYSTEMS
        ]
        return [*seed_parts, *imported.values()]

    def list_parts_for_trim(self, trim_id: str) -> dict[str, list[PartCatalogItem]]:
        trim = self.get_trim(trim_id)
        grouped: dict[str, list[PartCatalogItem]] = {}
        for item in self.list_parts():
            if trim.platform not in item.compatible_platforms:
                continue
            if trim.transmission not in item.compatible_transmissions and "any" not in item.compatible_transmissions:
                continue
            grouped.setdefault(item.subsystem, []).append(item)
        return {
            subsystem: sorted(items, key=lambda item: (item.cost_usd, item.label))
            for subsystem, items in grouped.items()
        }

    def get_part(self, part_id: str) -> PartCatalogItem:
        imported = self._part_record(part_id)
        if imported is not None:
            return imported.part
        seed_part = PARTS.get(part_id)
        if seed_part is None:
            raise KeyError(part_id)
        if not self._seed_fallback_allowed(seed_part.subsystem):
            raise KeyError(part_id)
        return seed_part

    def get_part_record(self, part_id: str) -> CanonicalPartRecord | None:
        return self._part_record(part_id)

    def list_price_snapshots(self, part_id: str) -> list[CanonicalPriceSnapshot]:
        record = self._part_record(part_id)
        if record is not None:
            return record.prices
        seed_part = PARTS.get(part_id)
        if seed_part is None or not self._seed_fallback_allowed(seed_part.subsystem):
            return []
        return [
            CanonicalPriceSnapshot(
                snapshot_id=f"seed_price_{seed_part.part_id}",
                part_id=seed_part.part_id,
                source="seed_catalog",
                provider="seed_catalog",
                source_id="seed_catalog",
                source_record_id=seed_part.part_id,
                import_run_id="seed_parts_2026q2",
                source_mode="seed",
                price_usd=float(seed_part.cost_usd),
                availability="catalog_seed",
                observed_at="2026-04-04T10:05:00Z",
                provenance_summary="Seed catalog fallback pricing.",
            )
        ]

    def get_preset(self, preset_id: str) -> BuildPreset:
        return self._seed.get_preset(preset_id)

    def list_presets(self) -> list[BuildPreset]:
        return self._seed.list_presets()

    def list_scenarios(self) -> list[ScenarioDefinition]:
        return self._seed.list_scenarios()

    def get_scenario(self, scenario_name: str) -> ScenarioDefinition:
        return self._seed.get_scenario(scenario_name)

    def list_engine_families(self) -> list[EngineFamily]:
        imported = [
            record.engine_family
            for record in self._store.list_engine_family_records()
            if record.provenance.source_id == "licensed_fixture_catalog"
        ]
        return imported or self._seed.list_engine_families()

    def get_engine_family(self, engine_family_id: str) -> EngineFamily:
        record = self._store.get_engine_family_record(engine_family_id)
        if record is not None:
            return record.engine_family
        if self._store.list_engine_family_records():
            raise KeyError(engine_family_id)
        return self._seed.get_engine_family(engine_family_id)

    def get_default_engine_config(self, trim_id: str) -> EngineBuildSpec:
        vehicle = self._vehicle_record(trim_id)
        if vehicle is not None:
            return self.get_engine_config(vehicle.default_engine_config_id)
        if self._imported_vehicles():
            raise KeyError(trim_id)
        return self._seed.get_default_engine_config(trim_id)

    def get_engine_config(self, config_id: str) -> EngineBuildSpec:
        record = self._store.get_engine_config_record(config_id)
        if record is not None:
            return record.engine_config
        if self._store.list_engine_config_records():
            raise KeyError(config_id)
        return self._seed.get_engine_config(config_id)

    def list_drivetrain_configs(self) -> list[DrivetrainConfig]:
        imported = [
            record.drivetrain_config
            for record in self._store.list_drivetrain_records()
            if record.provenance.source_id == "licensed_fixture_catalog"
        ]
        return imported or self._seed.list_drivetrain_configs()

    def get_default_drivetrain_config(self, trim_id: str) -> DrivetrainConfig:
        vehicle = self._vehicle_record(trim_id)
        if vehicle is not None:
            return self.get_drivetrain_config(vehicle.default_drivetrain_config_id)
        if self._imported_vehicles():
            raise KeyError(trim_id)
        return self._seed.get_default_drivetrain_config(trim_id)

    def get_drivetrain_config(self, config_id: str) -> DrivetrainConfig:
        record = self._store.get_drivetrain_record(config_id)
        if record is not None:
            return record.drivetrain_config
        if self._store.list_drivetrain_records():
            raise KeyError(config_id)
        return self._seed.get_drivetrain_config(config_id)

    def list_import_batches(self) -> list[ImportBatch]:
        imported_runs = self._store.list_import_runs()
        if imported_runs:
            return [
                ImportBatch(
                    import_batch_id=run.import_run_id,
                    source_system=run.source_id,
                    imported_at=run.completed_at or run.requested_at,
                    status="complete" if run.status == "succeeded" else "pending",
                    record_count=run.normalized_record_count,
                    notes="Imported catalog run.",
                )
                for run in imported_runs
            ]
        return self._seed.list_import_batches()

    def lookup_vin(self, vin: str) -> DecodedVehicle | None:
        return self._seed.lookup_vin(vin)

    def find_trim_by_vehicle(
        self,
        *,
        year: int | None,
        make: str | None,
        model: str | None,
        trim: str | None = None,
    ) -> VehicleTrim | None:
        candidates = [
            item
            for item in self.list_trims()
            if (year is None or item.year == year)
            and (make is None or item.make.lower() == make.lower())
            and (model is None or item.model.lower() == model.lower())
        ]
        if trim:
            for candidate in candidates:
                if candidate.trim.lower() == trim.lower():
                    return candidate
        return candidates[0] if candidates else None


@lru_cache
def get_repository() -> CatalogRepository:
    return CatalogRepository()
