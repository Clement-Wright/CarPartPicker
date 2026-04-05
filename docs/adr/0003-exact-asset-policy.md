# ADR 0003: Exact Asset Readiness Policy

## Status

Accepted

## Context

The long-term product direction requires exact 3D part models, not representative placeholders. The current viewport is intentionally proxy-based and should not be mistaken for production-ready asset coverage.

## Decision

A part is only `production_ready` for 3D assembly when all of the following exist:

- an approved exact mesh asset
- approved materials
- attachment anchors
- a collision proxy
- orientation and scale QA metadata

Until then, a part remains either:

- `seed_proxy_only`
- `missing_exact_asset`
- `qa_blocked`

## Consequences

- Asset readiness is surfaced through the production API.
- Simulation and compatibility can progress ahead of exact meshes, but production scene assembly cannot claim exact fidelity without approved assets.
- The current viewport remains valid for seed mode while making its limitations explicit.
