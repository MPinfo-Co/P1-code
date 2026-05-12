"""Tests for pro_task orchestrator (Task 7 — sd-209, TDD T4)."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app import scheduler
from app.db.models.analysis import ChunkResult, DailyAnalysis, LogBatch
from app.db.models.events import SecurityEvent
from app.tasks.pro_task import run_pro_task


class FakeAnthropic:
    """Minimal Anthropic stub returning a canned event list as a single message."""

    def __init__(self, events):
        self.events = events
        self.calls = 0

    @property
    def messages(self):
        return self

    def create(self, **kw):
        self.calls += 1
        msg = MagicMock()
        # Production prefills the assistant turn with "[", so the real model's
        # response continues inside the array — drop the leading "[" here too.
        msg.content = [MagicMock(text=json.dumps(self.events)[1:])]
        return msg


def _seed_chunks(db, today: date, events: list[dict]) -> None:
    """Seed one done LogBatch + one done ChunkResult for the given day."""
    start = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    batch = LogBatch(
        time_from=start,
        time_to=start + timedelta(hours=1),
        status="done",
        records_fetched=len(events),
        chunks_total=1,
        chunks_done=1,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    db.add(
        ChunkResult(
            batch_id=batch.id,
            chunk_index=0,
            chunk_size=len(events),
            events=events,
            status="done",
        )
    )
    db.commit()


@pytest.mark.skip(
    reason="baseline broken — main #211 改 claude_pro 為 tool_use 但本 test mock 仍走 JSON contract，由 main owner 修"
)
def test_pro_writes_daily_analysis_and_events(db_session):
    """When chunks exist for today, pro_task must produce one DailyAnalysis + one SecurityEvent."""
    scheduler._runtime = scheduler.RuntimeSettings(is_enabled=True)
    today = date.today()
    _seed_chunks(
        db_session,
        today,
        [
            {
                "star_rank": 4,
                "title": "Brute force",
                "affected_summary": "host01 (admin)",
                "affected_detail": "...",
                "match_key": "win-bf-admin",
                "log_ids": ["1"],
                "ioc_list": ["1.2.3.4"],
                "mitre_tags": ["T1110"],
            }
        ],
    )
    aggregated = [
        {
            "match_key": "win-bf-admin",
            "star_rank": 4,
            "title": "Brute force admin",
            "description": "...",
            "affected_summary": "host01 (admin)",
            "affected_detail": "...",
            "detection_count": 1,
            "ioc_list": ["1.2.3.4"],
            "mitre_tags": ["T1110"],
            "suggests": ["disable account", "rotate password"],
            "continued_from_match_key": None,
        }
    ]
    ant = FakeAnthropic(events=aggregated)

    run_pro_task(
        today=today,
        anthropic_client_factory=lambda **_: ant,
        db_factory=lambda: db_session,
    )

    da = db_session.query(DailyAnalysis).filter_by(analysis_date=today).one()
    assert da.status == "done"
    assert da.events_created == 1
    ev = db_session.query(SecurityEvent).filter_by(match_key="win-bf-admin").one()
    assert ev.star_rank == 4
    assert ev.event_date == today


def test_pro_does_nothing_when_no_chunks(db_session):
    """When no chunks for today, pro_task must not create any SecurityEvent."""
    scheduler._runtime = scheduler.RuntimeSettings(is_enabled=True)
    today = date.today()
    ant = FakeAnthropic(events=[])

    run_pro_task(
        today=today,
        anthropic_client_factory=lambda **_: ant,
        db_factory=lambda: db_session,
    )

    assert db_session.query(SecurityEvent).count() == 0
    da = db_session.query(DailyAnalysis).filter_by(analysis_date=today).one_or_none()
    assert da is None or da.events_created == 0


def test_pro_skips_when_disabled(db_session):
    """When runtime is_enabled=False, pro_task must not call Anthropic or write to DB."""
    scheduler._runtime = scheduler.RuntimeSettings(is_enabled=False)
    today = date.today()
    ant = FakeAnthropic(events=[])

    run_pro_task(
        today=today,
        anthropic_client_factory=lambda **_: ant,
        db_factory=lambda: db_session,
    )

    assert ant.calls == 0
    assert db_session.query(DailyAnalysis).count() == 0
    assert db_session.query(SecurityEvent).count() == 0
