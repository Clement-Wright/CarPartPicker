# ADR 0002: Production Data Model Direction

## Status

Accepted

## Context

The current prototype keeps catalog data in Python seed modules and build state in process memory. That is fast for prototyping, but it does not support durable builds, large-scale ingest, or the broader domain model required for production fitment and exact asset workflows.

## Decision

Production data is modeled around these durable concepts:

- `vehicle` and `vehicle_application`
- `part`, `part_application`, and `part_interface`
- `digital_asset`
- `price_snapshot`
- `build_state`
- `catalog_source`

`PostgreSQL` is the system of record. JSON-capable columns are allowed for early flexibility, but the model is intentionally centered on durable identifiers and queryable relationships rather than opaque blobs alone.

## Consequences

- The repository gains Alembic-managed schema scaffolding immediately.
- Build persistence moves from memory-first to database-capable storage with an in-memory fallback for local seed mode.
- Catalog import work can land incrementally without forcing a full rewrite of the planner surface.
