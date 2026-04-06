from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache

from app.catalog_import_schemas import CanonicalPartRecord, CanonicalVehicleRecord


@dataclass(frozen=True)
class VehicleIndexDocument:
    vehicle_id: str
    label: str
    platform: str
    transmission: str
    body_style: str
    search_text: str


@dataclass(frozen=True)
class PartIndexDocument:
    part_id: str
    subsystem: str
    label: str
    brand: str
    tags: tuple[str, ...]
    compatible_vehicle_ids: tuple[str, ...]
    search_text: str


class CatalogIndex(ABC):
    @abstractmethod
    def index_vehicle(self, record: CanonicalVehicleRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def index_part(self, record: CanonicalPartRecord) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear_source(self, source_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def search_vehicle_ids(self, *, query: str | None = None, transmission: str | None = None) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def search_part_ids(
        self,
        *,
        query: str | None = None,
        subsystem: str | None = None,
        tag: str | None = None,
        vehicle_id: str | None = None,
    ) -> list[str]:
        raise NotImplementedError


class InMemoryCatalogIndex(CatalogIndex):
    def __init__(self) -> None:
        self._vehicles: dict[str, VehicleIndexDocument] = {}
        self._parts: dict[str, PartIndexDocument] = {}

    def index_vehicle(self, record: CanonicalVehicleRecord) -> None:
        self._vehicles[record.vehicle_id] = VehicleIndexDocument(
            vehicle_id=record.vehicle_id,
            label=record.label,
            platform=record.vehicle.platform,
            transmission=record.vehicle.transmission,
            body_style=record.vehicle.body_style,
            search_text=f"{record.label} {record.vehicle_id} {record.vehicle.platform}".lower(),
        )

    def index_part(self, record: CanonicalPartRecord) -> None:
        self._parts[record.part_id] = PartIndexDocument(
            part_id=record.part_id,
            subsystem=record.subsystem,
            label=record.label,
            brand=record.part.brand,
            tags=tuple(record.part.tags),
            compatible_vehicle_ids=tuple(application.vehicle_id for application in record.applications),
            search_text=f"{record.label} {record.part.brand} {record.part.notes} {record.part_id}".lower(),
        )

    def clear_source(self, source_id: str) -> None:
        self._vehicles.clear()
        self._parts.clear()

    def search_vehicle_ids(self, *, query: str | None = None, transmission: str | None = None) -> list[str]:
        items = list(self._vehicles.values())
        if query:
            query_lower = query.lower()
            items = [item for item in items if query_lower in item.search_text]
        if transmission:
            items = [item for item in items if item.transmission == transmission]
        items.sort(key=lambda item: item.label)
        return [item.vehicle_id for item in items]

    def search_part_ids(
        self,
        *,
        query: str | None = None,
        subsystem: str | None = None,
        tag: str | None = None,
        vehicle_id: str | None = None,
    ) -> list[str]:
        items = list(self._parts.values())
        if query:
            query_lower = query.lower()
            items = [item for item in items if query_lower in item.search_text]
        if subsystem:
            items = [item for item in items if item.subsystem == subsystem]
        if tag:
            items = [item for item in items if tag in item.tags]
        if vehicle_id:
            items = [item for item in items if vehicle_id in item.compatible_vehicle_ids]
        items.sort(key=lambda item: (item.subsystem, item.label))
        return [item.part_id for item in items]


@lru_cache
def get_catalog_index() -> CatalogIndex:
    return InMemoryCatalogIndex()

