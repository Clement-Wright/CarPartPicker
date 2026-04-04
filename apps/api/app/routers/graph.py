from __future__ import annotations

from fastapi import APIRouter

from app.schemas import GraphResponse
from app.services.graph_service import build_graph

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/{graph_id}", response_model=GraphResponse)
def graph_detail(graph_id: str) -> GraphResponse:
    return build_graph(graph_id)

