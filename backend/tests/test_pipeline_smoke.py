"""End-to-end smoke test: Haiku task -> Pro task on the same in-memory DB.

Mocks the SSB client and Anthropic API so no network calls are made. Verifies
that LogBatch + ChunkResult rows from the Haiku run are picked up by the Pro
task and folded into a DailyAnalysis row plus a single SecurityEvent.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app import scheduler
from app.db.models.analysis import ChunkResult, DailyAnalysis, LogBatch
from app.db.models.events import SecurityEvent
from app.tasks.haiku_task import run_haiku_task
from app.tasks.pro_task import run_pro_task


class _FakeSSB:
    """SSB client stub returning two minimal logs (no FortiGate/Windows prefixes)."""

    def fetch_logs(self, **_):
        return [
            {"id": "1", "message": "logon failed", "dynamic_columns": {}},
            {"id": "2", "message": "explicit creds", "dynamic_columns": {}},
        ]


def _mk_ant(events: list[dict]) -> MagicMock:
    """Return an Anthropic mock whose `.messages.create` yields the given events."""
    a = MagicMock()
    a.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps(events))]
    )
    return a


def test_smoke_haiku_then_pro(db_session):
    """Run the Haiku orchestrator then the Pro orchestrator and verify both writes."""
    scheduler._runtime = scheduler.RuntimeSettings(
        is_enabled=True,
        ssb_host="https://h",
        ssb_logspace="ALL",
        ssb_username="u",
        ssb_password="p",
    )

    haiku_events = [
        {
            "star_rank": 3,
            "title": "Failed logons",
            "affected_summary": "host (admin)",
            "affected_detail": "...",
            "match_key": "win-bf-admin",
            "log_ids": ["1", "2"],
            "ioc_list": [],
            "mitre_tags": ["T1110"],
        }
    ]
    sonnet_events = [
        {
            **haiku_events[0],
            "description": "merged",
            "detection_count": 2,
            "suggests": ["lock", "rotate"],
            "continued_from_match_key": None,
        }
    ]

    run_haiku_task(
        ssb_client_factory=lambda **_: _FakeSSB(),
        anthropic_client_factory=lambda **_: _mk_ant(haiku_events),
        db_factory=lambda: db_session,
    )

    run_pro_task(
        today=datetime.now(timezone.utc).date(),
        anthropic_client_factory=lambda: _mk_ant(sonnet_events),
        db_factory=lambda: db_session,
    )

    assert db_session.query(LogBatch).count() == 1
    assert db_session.query(ChunkResult).count() >= 1
    assert db_session.query(DailyAnalysis).count() == 1
    assert (
        db_session.query(SecurityEvent).filter_by(match_key="win-bf-admin").count() == 1
    )
