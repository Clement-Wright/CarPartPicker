from __future__ import annotations

from app.schemas import BuildState, PatchEngineRequest
from app.services.build_state_service import patch_engine
from app.services.seed_repository import CatalogRepository


def apply_engine_builder_patch(
    build_id: str,
    request: PatchEngineRequest,
    repository: CatalogRepository | None = None,
) -> BuildState:
    return patch_engine(build_id, request, repository=repository)
