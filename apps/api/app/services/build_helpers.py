from __future__ import annotations

from app.schemas import BuildState, BuildSubsystemSelection, EngineFamily, PartCatalogItem
from app.services.seed_repository import CatalogRepository, get_repository


def selection_map(build: BuildState) -> dict[str, BuildSubsystemSelection]:
    return {item.subsystem: item for item in build.selections}


def selected_parts(build: BuildState, repository: CatalogRepository | None = None) -> dict[str, PartCatalogItem]:
    repository = repository or get_repository()
    return {
        item.subsystem: repository.get_part(item.selected_part_id)
        for item in build.selections
        if item.selected_part_id is not None
    }


def stock_part_ids(build: BuildState) -> dict[str, str]:
    return {item.subsystem: item.stock_part_id for item in build.base_config.stock_parts}


def stock_config_ids(build: BuildState) -> dict[str, str]:
    return {item.subsystem: item.stock_config_id for item in build.base_config.stock_configs}


def active_engine_family(build: BuildState, repository: CatalogRepository | None = None) -> EngineFamily:
    repository = repository or get_repository()
    return repository.get_engine_family(build.engine_build_spec.engine_family_id)


def stock_parts(build: BuildState, repository: CatalogRepository | None = None) -> dict[str, PartCatalogItem]:
    repository = repository or get_repository()
    return {subsystem: repository.get_part(part_id) for subsystem, part_id in stock_part_ids(build).items()}


def active_part(build: BuildState, subsystem: str, repository: CatalogRepository | None = None) -> PartCatalogItem:
    return selected_parts(build, repository)[subsystem]
