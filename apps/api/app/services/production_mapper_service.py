from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

from fastapi import HTTPException

from app.production_schemas import (
    CatalogSourceContract,
    CatalogSourceContractsResponse,
    PartDetailV1,
    PartPricesResponse,
    PartSearchResponse,
    PartSummaryV1,
    PriceSnapshotView,
    ProxyGeometry,
    ReadinessNote,
    SceneDimensions,
    SourceRecordSummary,
    VehicleDetailV1,
    VehicleSearchItem,
    VehicleSearchResponse,
    VisualizationMode,
)
from app.catalog_import_schemas import SUPPORTED_IMPORTED_PART_SUBSYSTEMS
from app.schemas import PartCatalogItem
from app.services.catalog_index_service import get_catalog_index
from app.services.seed_repository import CatalogRepository, get_repository


CATALOG_ONLY_SUBSYSTEMS = {"tune", "fuel_system", "clutch", "differential"}
PROXY_SUBSYSTEMS = {
    "body_aero",
    "forced_induction",
    "intake",
    "exhaust",
    "cooling",
    "transmission",
    "suspension",
    "brakes",
    "wheels",
    "tires",
}


@dataclass(frozen=True)
class VisualizationProfile:
    mode: VisualizationMode
    has_exact_mesh: bool
    has_proxy_geometry: bool
    has_dimensional_specs: bool
    scene_renderable: bool
    catalog_visible: bool
    anchor_slot: str | None
    proxy_geometry: ProxyGeometry | None
    dimensions: SceneDimensions
    mesh_url: str | None
    notes: list[ReadinessNote]


def _record_summary(provenance) -> SourceRecordSummary | None:
    if provenance is None:
        return None
    return SourceRecordSummary(
        source_id=provenance.source_id,
        provider=provenance.provider,
        source_record_id=provenance.source_record_id,
        import_run_id=provenance.import_run_id,
        verification_status=provenance.verification_status,
        observed_at=provenance.observed_at,
        updated_at=provenance.updated_at,
        summary=provenance.summary,
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _inch_to_mm(value: float | None) -> float | None:
    return None if value is None else value * 25.4


def _infer_part_diameter_mm(part: PartCatalogItem) -> float | None:
    direct = _inch_to_mm(part.geometry.wheel_diameter_in)
    if direct is not None:
        return direct

    label_match = re.search(r"(\d{2})-inch", part.label.lower())
    if label_match:
        return float(label_match.group(1)) * 25.4

    kind_match = re.search(r"(\d{2})", part.visual.kind.lower())
    if kind_match:
        return float(kind_match.group(1)) * 25.4

    return None


def _proxy_dimensions(part: PartCatalogItem) -> SceneDimensions:
    subsystem = part.subsystem
    if subsystem == "wheels":
        diameter_mm = _infer_part_diameter_mm(part) or 431.8
        width_mm = _inch_to_mm(part.geometry.wheel_width_in) or 203.2
        return SceneDimensions(length_mm=diameter_mm, width_mm=width_mm, height_mm=diameter_mm)
    if subsystem == "tires":
        width_mm = part.geometry.tire_width_mm or 225.0
        diameter_mm = (_infer_part_diameter_mm(part) or 431.8) + (width_mm * 0.36)
        return SceneDimensions(length_mm=diameter_mm, width_mm=width_mm, height_mm=diameter_mm)
    if subsystem == "brakes":
        diameter_mm = max(300.0, (part.geometry.brake_min_wheel_in or 17.0) * 19.0)
        return SceneDimensions(length_mm=diameter_mm, width_mm=32.0, height_mm=diameter_mm)
    if subsystem == "cooling":
        return SceneDimensions(length_mm=720.0, width_mm=80.0, height_mm=180.0)
    if subsystem == "body_aero":
        return SceneDimensions(length_mm=1600.0, width_mm=80.0, height_mm=140.0)
    if subsystem == "forced_induction":
        return SceneDimensions(length_mm=360.0, width_mm=360.0, height_mm=340.0)
    if subsystem == "intake":
        return SceneDimensions(length_mm=420.0, width_mm=180.0, height_mm=160.0)
    if subsystem == "exhaust":
        return SceneDimensions(length_mm=1200.0, width_mm=140.0, height_mm=140.0)
    if subsystem == "transmission":
        return SceneDimensions(length_mm=720.0, width_mm=420.0, height_mm=400.0)
    if subsystem == "suspension":
        return SceneDimensions(length_mm=520.0, width_mm=180.0, height_mm=140.0)
    return SceneDimensions()


def _has_dimensional_specs(part: PartCatalogItem, dimensions: SceneDimensions) -> bool:
    if any(value > 0 for value in (dimensions.length_mm, dimensions.width_mm, dimensions.height_mm)):
        return True
    geometry = part.geometry
    return any(
        value is not None and value > 0
        for value in (
            geometry.wheel_diameter_in,
            geometry.wheel_width_in,
            geometry.tire_width_mm,
            geometry.brake_min_wheel_in,
            geometry.hood_clearance_needed_mm,
            geometry.hood_clearance_gain_mm,
            geometry.ride_height_drop_mm,
            geometry.thermal_load,
        )
    )


def _proxy_geometry(part: PartCatalogItem, dimensions: SceneDimensions) -> ProxyGeometry | None:
    if part.subsystem == "wheels":
        return ProxyGeometry(
            kind="cylinder",
            color=part.visual.color,
            radius_mm=max(dimensions.length_mm, dimensions.height_mm) / 2,
            width_mm=dimensions.width_mm,
        )
    if part.subsystem == "tires":
        return ProxyGeometry(
            kind="cylinder",
            color=part.visual.color,
            radius_mm=max(dimensions.length_mm, dimensions.height_mm) / 2,
            width_mm=dimensions.width_mm,
        )
    if part.subsystem == "brakes":
        return ProxyGeometry(
            kind="disc",
            color=part.visual.color,
            radius_mm=max(dimensions.length_mm, dimensions.height_mm) / 2,
            thickness_mm=dimensions.width_mm,
        )
    if part.subsystem == "exhaust":
        return ProxyGeometry(
            kind="cylinder",
            color=part.visual.color,
            radius_mm=max(dimensions.width_mm, dimensions.height_mm) / 2,
            length_mm=dimensions.length_mm,
        )
    if any(value > 0 for value in (dimensions.length_mm, dimensions.width_mm, dimensions.height_mm)):
        return ProxyGeometry(
            kind="box",
            color=part.visual.color,
            size_mm=(dimensions.length_mm, dimensions.height_mm, dimensions.width_mm),
        )
    return None


def _default_anchor_slot(part: PartCatalogItem) -> str:
    if part.subsystem == "transmission":
        return "transmission_tunnel"
    if part.subsystem == "brakes":
        return "front_left_brake"
    if part.subsystem in {"wheels", "tires"}:
        return "front_left_hub"
    return part.visual.slot


def describe_part_visualization(part: PartCatalogItem, *, repository: CatalogRepository | None = None) -> VisualizationProfile:
    repository = repository or get_repository()
    record = repository.get_part_record(part.part_id) if hasattr(repository, "get_part_record") else None
    if record is not None:
        asset = record.asset_coverage
        return VisualizationProfile(
            mode=asset.visualization_mode,
            has_exact_mesh=asset.visualization_mode == "exact_mesh_ready",
            has_proxy_geometry=asset.proxy_geometry is not None,
            has_dimensional_specs=any(
                value > 0 for value in (asset.dimensions.length_mm, asset.dimensions.width_mm, asset.dimensions.height_mm)
            ),
            scene_renderable=asset.scene_renderable,
            catalog_visible=asset.catalog_visible,
            anchor_slot=asset.anchor_slot,
            proxy_geometry=asset.proxy_geometry,
            dimensions=asset.dimensions,
            mesh_url=asset.mesh_url,
            notes=[
                ReadinessNote(code=f"asset-{index}", message=note)
                for index, note in enumerate(asset.notes or [], start=1)
            ]
            or [
                ReadinessNote(
                    code="imported-asset-policy",
                    message="Visualization policy is sourced from the imported catalog asset manifest.",
                )
            ],
        )

    dimensions = _proxy_dimensions(part)
    has_dimensional_specs = _has_dimensional_specs(part, dimensions)
    proxy_geometry = _proxy_geometry(part, dimensions)

    if part.subsystem in CATALOG_ONLY_SUBSYSTEMS:
        return VisualizationProfile(
            mode="catalog_only",
            has_exact_mesh=False,
            has_proxy_geometry=False,
            has_dimensional_specs=has_dimensional_specs,
            scene_renderable=False,
            catalog_visible=True,
            anchor_slot=_default_anchor_slot(part),
            proxy_geometry=None,
            dimensions=dimensions,
            mesh_url=None,
            notes=[
                ReadinessNote(
                    code="catalog-only-supported",
                    message=f"{part.label} remains fully usable in the catalog, compatibility engine, build list, pricing, and simulation layers.",
                ),
                ReadinessNote(
                    code="scene-omitted",
                    message="This part is intentionally omitted from the 3D scene because exact placement data is not necessary or not yet available.",
                ),
            ],
        )

    if part.subsystem in PROXY_SUBSYSTEMS and has_dimensional_specs and proxy_geometry is not None:
        return VisualizationProfile(
            mode="proxy_from_dimensions",
            has_exact_mesh=False,
            has_proxy_geometry=True,
            has_dimensional_specs=True,
            scene_renderable=True,
            catalog_visible=True,
            anchor_slot=_default_anchor_slot(part),
            proxy_geometry=proxy_geometry,
            dimensions=dimensions,
            mesh_url=None,
            notes=[
                ReadinessNote(
                    code="proxy-from-dimensions",
                    message=f"{part.label} renders as a dimension-driven proxy until an exact public or licensed mesh is available.",
                )
            ],
        )

    if has_dimensional_specs and proxy_geometry is not None:
        return VisualizationProfile(
            mode="proxy_from_dimensions",
            has_exact_mesh=False,
            has_proxy_geometry=True,
            has_dimensional_specs=True,
            scene_renderable=True,
            catalog_visible=True,
            anchor_slot=_default_anchor_slot(part),
            proxy_geometry=proxy_geometry,
            dimensions=dimensions,
            mesh_url=None,
            notes=[
                ReadinessNote(
                    code="proxy-fallback",
                    message=f"{part.label} is renderable through a simplified dimensional proxy.",
                )
            ],
        )

    return VisualizationProfile(
        mode="unsupported",
        has_exact_mesh=False,
        has_proxy_geometry=False,
        has_dimensional_specs=has_dimensional_specs,
        scene_renderable=False,
        catalog_visible=False,
        anchor_slot=_default_anchor_slot(part),
        proxy_geometry=None,
        dimensions=dimensions,
        mesh_url=None,
        notes=[
            ReadinessNote(
                code="unsupported-data-gap",
                message="This record is held back because it lacks enough trusted visualization or spec metadata for user-facing support.",
            )
        ],
    )


def map_part_summary(part: PartCatalogItem, repository: CatalogRepository | None = None) -> PartSummaryV1:
    repository = repository or get_repository()
    visualization = describe_part_visualization(part, repository=repository)
    record = repository.get_part_record(part.part_id) if hasattr(repository, "get_part_record") else None
    return PartSummaryV1(
        part_id=part.part_id,
        subsystem=part.subsystem,
        label=part.label,
        brand=part.brand,
        notes=part.notes,
        tags=part.tags,
        cost_usd=part.cost_usd,
        source_mode="licensed" if record is not None else "seed",
        production_ready=(record is not None and record.provenance.verification_status == "verified"),
        visualization_mode=visualization.mode,
        has_exact_mesh=visualization.has_exact_mesh,
        has_proxy_geometry=visualization.has_proxy_geometry,
        has_dimensional_specs=visualization.has_dimensional_specs,
        scene_renderable=visualization.scene_renderable,
        catalog_visible=visualization.catalog_visible,
        geometry=part.geometry.model_dump(),
        performance=part.performance.model_dump(),
        visualization_notes=visualization.notes,
        record_provenance=_record_summary(record.provenance if record is not None else None),
    )


def map_part_detail(part: PartCatalogItem, repository: CatalogRepository | None = None) -> PartDetailV1:
    summary = map_part_summary(part, repository=repository)
    return PartDetailV1(
        **summary.model_dump(),
        compatible_platforms=part.compatible_platforms,
        compatible_transmissions=list(part.compatible_transmissions),
        interface=part.interface.model_dump(),
        capabilities=part.capabilities,
        dependency_rules=[rule.model_dump() for rule in part.dependency_rules],
        visual=part.visual.model_dump(),
    )


def list_parts_v1(
    *,
    query: str | None = None,
    subsystem: str | None = None,
    tag: str | None = None,
    vehicle_id: str | None = None,
    renderable_only: bool = False,
    repository: CatalogRepository | None = None,
) -> PartSearchResponse:
    repository = repository or get_repository()
    imported_ids = get_catalog_index().search_part_ids(
        query=query,
        subsystem=subsystem if subsystem in SUPPORTED_IMPORTED_PART_SUBSYSTEMS or subsystem is None else None,
        tag=tag,
        vehicle_id=vehicle_id,
    )
    imported_items = [repository.get_part(part_id) for part_id in imported_ids]

    seed_candidates = [
        item
        for item in repository.list_parts()
        if item.subsystem not in SUPPORTED_IMPORTED_PART_SUBSYSTEMS
    ]
    if vehicle_id:
        try:
            vehicle = repository.get_trim(vehicle_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown vehicle.") from exc
        seed_candidates = [
            item
            for item in seed_candidates
            if vehicle.platform in item.compatible_platforms
            and (vehicle.transmission in item.compatible_transmissions or "any" in item.compatible_transmissions)
        ]
    if query:
        query_lower = query.lower()
        seed_candidates = [
            item
            for item in seed_candidates
            if query_lower in item.label.lower()
            or query_lower in item.brand.lower()
            or query_lower in item.notes.lower()
            or query_lower in item.part_id.lower()
        ]
    if subsystem:
        if subsystem in SUPPORTED_IMPORTED_PART_SUBSYSTEMS:
            seed_candidates = []
        else:
            seed_candidates = [item for item in seed_candidates if item.subsystem == subsystem]
    if tag:
        seed_candidates = [item for item in seed_candidates if tag in item.tags]

    items = [*seed_candidates, *imported_items]
    mapped = [map_part_summary(item, repository=repository) for item in sorted(items, key=lambda part: (part.subsystem, part.cost_usd, part.label))]
    mapped = [item for item in mapped if item.catalog_visible]
    if renderable_only:
        mapped = [item for item in mapped if item.scene_renderable]
    source_mode = "licensed" if any(item.source_mode == "licensed" for item in mapped) else "seed"
    return PartSearchResponse(items=mapped, total=len(mapped), source_mode=source_mode)


def get_part_v1(part_id: str, repository: CatalogRepository | None = None) -> PartDetailV1:
    repository = repository or get_repository()
    try:
        part = repository.get_part(part_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown part.") from exc
    detail = map_part_detail(part, repository=repository)
    if not detail.catalog_visible:
        raise HTTPException(status_code=404, detail="Unknown part.")
    return detail


def get_part_prices_v1(part_id: str, repository: CatalogRepository | None = None) -> PartPricesResponse:
    repository = repository or get_repository()
    try:
        part = repository.get_part(part_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown part.") from exc
    snapshots = [
        PriceSnapshotView(
            source=item.source,
            source_mode=item.source_mode,
            provider=item.provider,
            source_id=item.source_id,
            source_record_id=item.source_record_id,
            import_run_id=item.import_run_id,
            price_usd=item.price_usd,
            currency=item.currency,
            availability=item.availability,
            product_url=item.product_url,
            observed_at=item.observed_at,
            provenance_summary=item.provenance_summary,
        )
        for item in repository.list_price_snapshots(part.part_id)
    ]
    if not snapshots:
        snapshots = [
            PriceSnapshotView(
                source="seed_catalog",
                source_mode="seed",
                provider="seed_catalog",
                source_id="seed_catalog",
                source_record_id=part.part_id,
                import_run_id="seed_parts_2026q2",
                price_usd=float(part.cost_usd),
                availability="catalog_seed",
                observed_at=_now_iso(),
                provenance_summary="Seed catalog fallback pricing.",
            )
        ]
    return PartPricesResponse(part_id=part.part_id, snapshots=snapshots)


def list_vehicles_v1(
    *,
    query: str | None = None,
    transmission: str | None = None,
    repository: CatalogRepository | None = None,
) -> VehicleSearchResponse:
    repository = repository or get_repository()
    vehicle_ids = get_catalog_index().search_vehicle_ids(query=query, transmission=transmission)
    items = []
    for vehicle_id in vehicle_ids:
        trim = repository.get_trim(vehicle_id)
        record = repository.get_vehicle_record(vehicle_id) if hasattr(repository, "get_vehicle_record") else None
        items.append(
            VehicleSearchItem(
                trim_id=trim.trim_id,
                label=f"{trim.year} {trim.make} {trim.model} {trim.trim}",
                platform=trim.platform,
                transmission=trim.transmission,
                body_style=trim.body_style,
                source_mode="licensed" if record is not None else "seed",
                record_provenance=_record_summary(record.provenance if record is not None else None),
            )
        )
    return VehicleSearchResponse(items=items, total=len(items), source_mode="licensed" if items else "seed")


def get_vehicle_v1(trim_id: str, repository: CatalogRepository | None = None) -> VehicleDetailV1:
    repository = repository or get_repository()
    try:
        trim = repository.get_trim(trim_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown vehicle.") from exc
    record = repository.get_vehicle_record(trim_id) if hasattr(repository, "get_vehicle_record") else None

    return VehicleDetailV1(
        vehicle=trim,
        source_mode="licensed" if record is not None else "seed",
        readiness_notes=(
            [
                ReadinessNote(
                    code="imported-vehicle-slice",
                    message="Vehicle coverage for this supported slice is served from the imported canonical catalog path.",
                )
            ]
            if record is not None
            else [
                ReadinessNote(
                    code="seed-vehicle-snapshot",
                    message="Vehicle coverage is currently served from seed-mode trim snapshots and should be replaced by licensed application data for production.",
                )
            ]
        ),
        record_provenance=_record_summary(record.provenance if record is not None else None),
    )


def catalog_source_contracts() -> CatalogSourceContractsResponse:
    return CatalogSourceContractsResponse(
        items=[
            CatalogSourceContract(
                source_id="autocare_aces_pies",
                provider="Auto Care",
                contract_type="autocare",
                status="contract_defined",
                description="Machine-readable fitment and product information exchange layer for North American aftermarket taxonomy.",
                required_fields=["brand_code", "part_terminology_id", "vehicle_configuration_id", "qualifiers", "attribute_payload"],
                notes=["Standards communicate product data, but application truth must still be researched or licensed."],
            ),
            CatalogSourceContract(
                source_id="nhtsa_vpic",
                provider="NHTSA",
                contract_type="vpic",
                status="contract_defined",
                description="VIN normalization and decode contract backed by local PostgreSQL snapshots or live API fallback.",
                required_fields=["vin", "make", "model", "model_year", "trim", "vehicle_type"],
                notes=["Standalone vPIC backups are used for VIN decode; richer attributes still require API access."],
            ),
            CatalogSourceContract(
                source_id="tecdoc_catalog",
                provider="TecAlliance",
                contract_type="tecdoc",
                status="contract_defined",
                description="Global article, linkage, and catalog import contract for aftermarket parts and applications.",
                required_fields=["article_id", "brand_id", "generic_article_id", "linkages", "criteria", "asset_refs"],
                notes=["Used as a licensed catalog backbone, not as the sole source of fitment truth."],
            ),
            CatalogSourceContract(
                source_id="vendor_feed",
                provider="Manufacturer or distributor",
                contract_type="vendor_feed",
                status="contract_defined",
                description="Authoritative vendor pricing, application, torque/load, and compliance feed.",
                required_fields=["sku", "application_set", "price", "currency", "availability", "compliance_tags"],
                notes=["Vendor feeds can override or refine secondary marketplace pricing."],
            ),
            CatalogSourceContract(
                source_id="exact_asset_manifest",
                provider="Asset operations",
                contract_type="exact_asset_manifest",
                status="contract_defined",
                description="Exact 3D asset manifest for licensed part meshes and QA state.",
                required_fields=["part_id", "mesh_uri", "material_set", "anchor_set", "collision_uri", "qa_status"],
                notes=["A part is not production-ready for exact assembly until this manifest passes QA."],
            ),
        ]
    )
