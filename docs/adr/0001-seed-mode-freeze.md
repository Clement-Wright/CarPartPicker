# ADR 0001: Freeze Current Product as Seed Mode

## Status

Accepted

## Context

The current CarPartPicker application is a meaningful prototype, but its catalog, fitment logic, pricing, and 3D scene are all seed-backed. The existing experience is useful for validating interaction design and service boundaries, but it does not yet meet the production bar required for licensed fitment data, exact digital assets, and validated simulation.

## Decision

We explicitly freeze the current experience as `seed mode`.

Seed mode means:

- Catalog data may be hand-curated or imported from non-production sources.
- Build compatibility remains deterministic, but not complete enough for real-world purchasing decisions.
- 3D scenes may render proxy geometry instead of licensed exact part meshes.
- Simulation outputs are useful for product development, but not yet calibrated enough for production claims.

## Consequences

- We keep the current planner working while building a production-oriented `v1` backend beside it.
- Every production-facing endpoint must clearly communicate whether data is `seed`, `licensed`, or `verified`.
- Exact-part readiness becomes a first-class requirement instead of an implicit future task.
