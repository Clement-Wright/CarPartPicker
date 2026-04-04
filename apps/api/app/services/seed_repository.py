from __future__ import annotations

from functools import lru_cache

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


class CatalogRepository:
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

    def list_parts_for_trim(self, trim_id: str) -> dict[str, list[PartCatalogItem]]:
        trim = self.get_trim(trim_id)
        grouped: dict[str, list[PartCatalogItem]] = {}
        for item in PARTS.values():
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

    def get_import_batch(self, import_batch_id: str) -> ImportBatch:
        return IMPORT_BATCHES[import_batch_id]

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


@lru_cache
def get_repository() -> CatalogRepository:
    return CatalogRepository()
