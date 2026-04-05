from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from app.production_schemas import (
    AssetReadiness,
    CatalogSourceContract,
    CatalogSourceContractsResponse,
    PartDetailV1,
    PartPricesResponse,
    PartSearchResponse,
    PartSummaryV1,
    PriceSnapshotView,
    ReadinessNote,
    VehicleDetailV1,
    VehicleSearchItem,
    VehicleSearchResponse,
)
from app.schemas import PartCatalogItem
from app.services.seed_repository import CatalogRepository, get_repository


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def seed_asset_readiness(*, subsystem: str, label: str) -> AssetReadiness:
    return AssetReadiness(
        status="seed_proxy_only",
        notes=[
            ReadinessNote(
                code="seed-proxy-only",
                message=f"{label} currently renders through seed-mode proxy geometry for the {subsystem} subsystem.",
            ),
            ReadinessNote(
                code="exact-asset-required",
                message="Production readiness requires an approved exact mesh, anchors, collision proxy, materials, and QA metadata.",
            ),
        ],
    )


def map_part_summary(part: PartCatalogItem) -> PartSummaryV1:
    asset_readiness = seed_asset_readiness(subsystem=part.subsystem, label=part.label)
    return PartSummaryV1(
        part_id=part.part_id,
        subsystem=part.subsystem,
        label=part.label,
        brand=part.brand,
        notes=part.notes,
        tags=part.tags,
        cost_usd=part.cost_usd,
        asset_readiness=asset_readiness,
        production_ready=asset_readiness.status == "approved_exact",
    )


def map_part_detail(part: PartCatalogItem) -> PartDetailV1:
    summary = map_part_summary(part)
    return PartDetailV1(
        **summary.model_dump(),
        compatible_platforms=part.compatible_platforms,
        compatible_transmissions=list(part.compatible_transmissions),
        interface=part.interface.model_dump(),
        geometry=part.geometry.model_dump(),
        performance=part.performance.model_dump(),
        capabilities=part.capabilities,
        dependency_rules=[rule.model_dump() for rule in part.dependency_rules],
        visual=part.visual.model_dump(),
    )


def list_parts_v1(
    *,
    query: str | None = None,
    subsystem: str | None = None,
    tag: str | None = None,
    repository: CatalogRepository | None = None,
) -> PartSearchResponse:
    repository = repository or get_repository()
    items = repository.list_parts()
    if query:
        query_lower = query.lower()
        items = [
            item
            for item in items
            if query_lower in item.label.lower()
            or query_lower in item.brand.lower()
            or query_lower in item.notes.lower()
            or query_lower in item.part_id.lower()
        ]
    if subsystem:
        items = [item for item in items if item.subsystem == subsystem]
    if tag:
        items = [item for item in items if tag in item.tags]

    mapped = [map_part_summary(item) for item in sorted(items, key=lambda part: (part.subsystem, part.cost_usd, part.label))]
    return PartSearchResponse(items=mapped, total=len(mapped))


def get_part_v1(part_id: str, repository: CatalogRepository | None = None) -> PartDetailV1:
    repository = repository or get_repository()
    try:
        part = repository.get_part(part_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown part.") from exc
    return map_part_detail(part)


def get_part_prices_v1(part_id: str, repository: CatalogRepository | None = None) -> PartPricesResponse:
    repository = repository or get_repository()
    try:
        part = repository.get_part(part_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown part.") from exc

    snapshots = [
        PriceSnapshotView(
            source="seed_catalog",
            source_mode="seed",
            price_usd=float(part.cost_usd),
            availability="catalog_seed",
            observed_at=_now_iso(),
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
    trims = repository.list_trims()
    if query:
        query_lower = query.lower()
        trims = [
            trim
            for trim in trims
            if query_lower in f"{trim.year} {trim.make} {trim.model} {trim.trim}".lower()
            or query_lower in trim.trim_id.lower()
            or query_lower in trim.platform.lower()
        ]
    if transmission:
        trims = [trim for trim in trims if trim.transmission == transmission]

    items = [
        VehicleSearchItem(
            trim_id=trim.trim_id,
            label=f"{trim.year} {trim.make} {trim.model} {trim.trim}",
            platform=trim.platform,
            transmission=trim.transmission,
            body_style=trim.body_style,
        )
        for trim in trims
    ]
    return VehicleSearchResponse(items=items, total=len(items))


def get_vehicle_v1(trim_id: str, repository: CatalogRepository | None = None) -> VehicleDetailV1:
    repository = repository or get_repository()
    try:
        trim = repository.get_trim(trim_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown vehicle.") from exc

    return VehicleDetailV1(
        vehicle=trim,
        readiness_notes=[
            ReadinessNote(
                code="seed-vehicle-snapshot",
                message="Vehicle coverage is currently served from seed-mode trim snapshots and should be replaced by licensed application data for production.",
            )
        ],
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
