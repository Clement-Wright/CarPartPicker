from __future__ import annotations

from app.schemas import GraphResponse
from app.services.graph_service import build_graph


def build_graph_reasoning(build_id: str) -> GraphResponse:
    return build_graph(build_id)
