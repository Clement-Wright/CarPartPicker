from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import csv
import json

from app.config import get_settings
from app.schemas import DecodedVehicle, PackageSeed, PartSeed, VehicleTrim


def _as_float(value: str | None) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def _as_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    return int(float(value))


class SeedRepository:
    def __init__(self, seed_dir: Path):
        self.seed_dir = seed_dir
        self._trims = self._load_trims()
        self._parts = self._load_parts()
        self._packages = self._load_packages()
        self._vins = self._load_vins()

    def _load_trims(self) -> dict[str, VehicleTrim]:
        path = self.seed_dir / "trims.csv"
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return {
                row["trim_id"]: VehicleTrim(
                    trim_id=row["trim_id"],
                    platform=row["platform"],
                    year=int(row["year"]),
                    make=row["make"],
                    model=row["model"],
                    trim=row["trim"],
                    drivetrain=row["drivetrain"],
                    transmission=row["transmission"],
                    body_style=row["body_style"],
                    stock_wheel_diameter=int(row["stock_wheel_diameter"]),
                    stock_tire=row["stock_tire"],
                    safety_index=_as_float(row["safety_index"]),
                    recall_burden=_as_float(row["recall_burden"]),
                    complaint_burden=_as_float(row["complaint_burden"]),
                    recall_summary=row["recall_summary"],
                    complaint_summary=row["complaint_summary"],
                    utility_note=row["utility_note"],
                    mod_potential=_as_float(row["mod_potential"]),
                )
                for row in reader
            }

    def _load_parts(self) -> dict[str, PartSeed]:
        path = self.seed_dir / "parts.csv"
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            return {
                row["part_id"]: PartSeed(
                    part_id=row["part_id"],
                    category=row["category"],
                    brand=row["brand"],
                    name=row["name"],
                    platforms=row["platforms"].split("|"),
                    wheel_diameter=_as_int(row["wheel_diameter"]),
                    requires_min_wheel_diameter=_as_int(
                        row["requires_min_wheel_diameter"]
                    ),
                    season=row["season"] or "all",
                    comfort_bias=_as_float(row["comfort_bias"]),
                    grip_bias=_as_float(row["grip_bias"]),
                    winter_bias=_as_float(row["winter_bias"]),
                    braking_bias=_as_float(row["braking_bias"]),
                    safety_delta=_as_float(row["safety_delta"]),
                    cost=int(row["cost"]),
                    notes=row["notes"],
                )
                for row in reader
            }

    def _load_packages(self) -> dict[str, PackageSeed]:
        path = self.seed_dir / "packages.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        packages = [PackageSeed.model_validate(item) for item in raw]
        return {package.package_id: package for package in packages}

    def _load_vins(self) -> dict[str, DecodedVehicle]:
        path = self.seed_dir / "vin_cache.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {
            item["vin"].upper(): DecodedVehicle(
                vin=item["vin"].upper(),
                trim_id=item["trim_id"],
                year=item["year"],
                make=item["make"],
                model=item["model"],
                trim=item["trim"],
                source="seed_cache",
                cache_hit=True,
            )
            for item in raw
        }

    def list_trims(self) -> list[VehicleTrim]:
        return sorted(
            self._trims.values(),
            key=lambda trim: (trim.year, trim.make, trim.model, trim.trim),
        )

    def get_trim(self, trim_id: str) -> VehicleTrim:
        return self._trims[trim_id]

    def list_packages(self) -> list[PackageSeed]:
        return list(self._packages.values())

    def get_package(self, package_id: str) -> PackageSeed:
        return self._packages[package_id]

    def get_part(self, part_id: str) -> PartSeed:
        return self._parts[part_id]

    def expand_parts(self, package: PackageSeed) -> list[PartSeed]:
        return [self.get_part(part_id) for part_id in package.part_ids]

    def lookup_vin(self, vin: str) -> DecodedVehicle | None:
        return self._vins.get(vin.upper())

    def find_trim_by_vehicle(
        self, *, year: int | None, make: str | None, model: str | None, trim: str | None = None
    ) -> VehicleTrim | None:
        candidates = [
            item
            for item in self._trims.values()
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
def get_repository() -> SeedRepository:
    return SeedRepository(get_settings().seed_dir)

