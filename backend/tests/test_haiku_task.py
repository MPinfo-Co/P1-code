"""Tests for haiku_task orchestrator (Task 6 — sd-209)."""
from unittest.mock import MagicMock
import json
from app import scheduler
from app.tasks.haiku_task import run_haiku_task
from app.db.models.analysis import LogBatch, ChunkResult


class FakeSSB:
    def __init__(self, logs):
        self.logs = logs
        self.calls = 0

    def fetch_logs(self, *, time_from, time_to, search_expression):
        self.calls += 1
        return self.logs


class FakeAnthropic:
    def __init__(self, events):
        self.events = events
        self.calls = 0

    @property
    def messages(self):
        return self  # mimic .messages.create

    def create(self, **kw):
        self.calls += 1
        msg = MagicMock()
        msg.content = [MagicMock(text=json.dumps(self.events))]
        return msg


def test_haiku_skips_when_disabled(db_session):
    scheduler._runtime = scheduler.RuntimeSettings(is_enabled=False)
    ssb = FakeSSB(logs=[{"id": "1"}])
    ant = FakeAnthropic(events=[])
    run_haiku_task(
        ssb_client_factory=lambda **_: ssb,
        anthropic_client_factory=lambda **_: ant,
        db_factory=lambda: db_session,
    )
    assert ssb.calls == 0
    assert db_session.query(LogBatch).count() == 0


def test_haiku_writes_batch_and_chunk_when_enabled(db_session):
    scheduler._runtime = scheduler.RuntimeSettings(
        is_enabled=True,
        ssb_host="https://h",
        ssb_logspace="ALL",
        ssb_username="u",
        ssb_password="p",
    )
    ssb = FakeSSB(logs=[{"id": str(i), "message": "x"} for i in range(3)])
    ant = FakeAnthropic(events=[{
        "star_rank": 3, "title": "Test event", "affected_summary": "host (test)",
        "affected_detail": "...", "match_key": "win-failed-logon",
        "log_ids": ["1"], "ioc_list": [], "mitre_tags": [],
    }])
    run_haiku_task(
        ssb_client_factory=lambda **_: ssb,
        anthropic_client_factory=lambda **_: ant,
        db_factory=lambda: db_session,
    )

    batches = db_session.query(LogBatch).all()
    assert len(batches) == 1
    b = batches[0]
    assert b.records_fetched == 3
    assert b.status == "done"
    chunks = db_session.query(ChunkResult).filter_by(batch_id=b.id).all()
    assert len(chunks) >= 1
    assert chunks[0].events
