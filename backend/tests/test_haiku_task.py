"""Tests for haiku_task orchestrator (Task 6 — sd-209)."""

from app import scheduler
from app.tasks.haiku_task import run_haiku_task
from app.db.models.analysis import LogBatch


class FakeSSB:
    def __init__(self, logs):
        self.logs = logs
        self.calls = 0

    def fetch_logs(self, *, time_from, time_to, search_expression):
        self.calls += 1
        return self.logs


def test_haiku_skips_when_disabled(db_session):
    scheduler._runtime = scheduler.RuntimeSettings(is_enabled=False)
    ssb = FakeSSB(logs=[{"id": "1"}])
    run_haiku_task(
        ssb_client_factory=lambda **_: ssb,
        anthropic_client_factory=lambda **_: None,
        db_factory=lambda: db_session,
    )
    assert ssb.calls == 0
    assert db_session.query(LogBatch).count() == 0
