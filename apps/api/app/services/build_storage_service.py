from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from functools import lru_cache
from threading import Lock

from sqlalchemy import delete

from app.config import get_settings
from app.db import BuildStateRecord, get_session_factory
from app.schemas import BuildState
from app.services.seed_repository import get_repository


class BuildStore(ABC):
    @abstractmethod
    def save(self, build: BuildState) -> BuildState:
        raise NotImplementedError

    @abstractmethod
    def get(self, build_id: str) -> BuildState | None:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError


class InMemoryBuildStore(BuildStore):
    def __init__(self) -> None:
        self._builds: dict[str, BuildState] = {}
        self._lock = Lock()

    def save(self, build: BuildState) -> BuildState:
        with self._lock:
            self._builds[build.build_id] = build
        return build

    def get(self, build_id: str) -> BuildState | None:
        return self._builds.get(build_id)

    def clear(self) -> None:
        with self._lock:
            self._builds.clear()


class SqlBuildStore(BuildStore):
    def save(self, build: BuildState) -> BuildState:
        session_factory = get_session_factory()
        if session_factory is None:
            raise RuntimeError("Database session factory is not configured.")

        payload = build.model_dump(mode="json")
        source_mode = "licensed" if get_repository().get_vehicle_record(build.vehicle.trim_id) is not None else "seed"
        with session_factory() as session:
            record = session.get(BuildStateRecord, build.build_id)
            if record is None:
                record = BuildStateRecord(
                    build_id=build.build_id,
                    build_hash=build.computation.build_hash,
                    revision=build.computation.revision,
                    source_mode=source_mode,
                    build_json=payload,
                )
                session.add(record)
            else:
                record.build_hash = build.computation.build_hash
                record.revision = build.computation.revision
                record.source_mode = source_mode
                record.build_json = payload
                record.updated_at = datetime.utcnow()
            session.commit()
        return build

    def get(self, build_id: str) -> BuildState | None:
        session_factory = get_session_factory()
        if session_factory is None:
            return None
        with session_factory() as session:
            record = session.get(BuildStateRecord, build_id)
            if record is None:
                return None
            return BuildState.model_validate(record.build_json)

    def clear(self) -> None:
        session_factory = get_session_factory()
        if session_factory is None:
            return
        with session_factory() as session:
            session.execute(delete(BuildStateRecord))
            session.commit()


@lru_cache
def get_build_store() -> BuildStore:
    settings = get_settings()
    if settings.build_storage_mode == "memory":
        return InMemoryBuildStore()
    if settings.postgres_url:
        return SqlBuildStore()
    return InMemoryBuildStore()


def reset_build_store() -> None:
    get_build_store().clear()
