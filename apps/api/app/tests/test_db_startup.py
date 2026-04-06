from __future__ import annotations

from sqlalchemy.exc import OperationalError

import app.db as db


class _FakeConnection:
    def __enter__(self) -> "_FakeConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def exec_driver_sql(self, statement: str) -> None:
        self.statement = statement


class _FlakyEngine:
    def __init__(self, fail_times: int) -> None:
        self.fail_times = fail_times
        self.connect_calls = 0

    def connect(self) -> _FakeConnection:
        self.connect_calls += 1
        if self.connect_calls <= self.fail_times:
            raise OperationalError("SELECT 1", {}, RuntimeError("database not ready"))
        return _FakeConnection()


def test_wait_for_db_retries_until_connection_succeeds(monkeypatch) -> None:
    engine = _FlakyEngine(fail_times=2)
    delays: list[float] = []

    monkeypatch.setattr(db, "get_engine", lambda: engine)
    monkeypatch.setattr(db, "sleep", lambda seconds: delays.append(seconds))

    db.wait_for_db(max_attempts=3, delay_seconds=0.25)

    assert engine.connect_calls == 3
    assert delays == [0.25, 0.25]
