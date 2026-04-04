from __future__ import annotations

from fastapi import APIRouter

from app.schemas import ParsedBuildQuery, QueryParseRequest
from app.services.query_parser import parse_build_query

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/parse", response_model=ParsedBuildQuery)
def parse_query(request: QueryParseRequest) -> ParsedBuildQuery:
    return parse_build_query(
        request.text,
        vehicle_context=request.vehicle_context,
        current_setup=None,
    )

