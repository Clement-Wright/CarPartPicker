from __future__ import annotations

from app.schemas import BuildMetricSnapshot, BuildState
from app.services.vehicle_metrics_service import build_vehicle_metric_snapshot


def build_metric_snapshot(build: BuildState) -> BuildMetricSnapshot:
    snapshot = build_vehicle_metric_snapshot(build)
    return BuildMetricSnapshot(**snapshot.model_dump())
