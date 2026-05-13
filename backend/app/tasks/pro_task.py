"""Sonnet Task — daily aggregation of chunk-level events into security_events.

Public entry: run_pro_task(*, today, anthropic_client_factory, db_factory)

The orchestrator gathers today's done ChunkResult rows, groups their events
by ``match_key``, asks Claude Sonnet to merge them against yesterday's open
events, then upserts the result into ``tb_security_events`` and records a
single ``tb_daily_analysis`` row for the run.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Callable

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import scheduler
from app.db.models.analysis import ChunkResult, DailyAnalysis, LogBatch
from app.db.models.events import SecurityEvent
from app.logger_utils.log_channels import get_system_logger
from app.tasks import claude_pro

logger = get_system_logger()


def _collect_today_events(db: Session, today: date) -> dict[str, list[dict]]:
    """Group today's done ChunkResult events by ``match_key``.

    Args:
        db: Active SQLAlchemy session.
        today: Date used to filter ``LogBatch.time_to`` (batch 結束時間落在 today
            才收進；以結束時間歸屬可避免跨日 batch（如 23:55–00:05 開始於昨天）
            被永遠漏掉）。

    Returns:
        Mapping from ``match_key`` to the list of raw events sharing it.
        Events without a ``match_key`` are dropped.
    """
    rows = (
        db.query(ChunkResult)
        .join(LogBatch, ChunkResult.batch_id == LogBatch.id)
        .filter(
            func.date(LogBatch.time_to) == today,
            ChunkResult.status == "done",
        )
        .all()
    )
    grouped: dict[str, list[dict]] = defaultdict(list)
    for cr in rows:
        for ev in cr.events or []:
            mk = ev.get("match_key")
            if mk:
                grouped[mk].append(ev)
    return dict(grouped)


def _recent_open_events_for_continuity(db: Session, today: date) -> list[dict]:
    """Return a digest of all still-open SecurityEvents before today, for
    Sonnet continuity detection (continued_from_match_key判斷).

    範圍：`event_date < today` AND `current_status` 為 `pending` 或
    `investigating`。撈整段歷史 open 事件（不只昨天），讓 Sonnet 有足夠
    context 判斷今天的事件是不是既有 open 事件的延續。實務上 open 事件
    數量通常不大、prompt 不會爆。

    註：SD spec `fn_expert_03_backend.md` 中描述「昨天的已確認事件」
    為過時用語，實際 continuity 設計是看「所有 open 歷史事件」；待
    SD spec 修正時同步更新（見 PG #206 audit 議題 #14）。

    Args:
        db: Active SQLAlchemy session.
        today: Cut-off date; events strictly before ``today`` are considered.

    Returns:
        Compact list of dicts with ``match_key``, ``title``, ``star_rank``,
        and ``event_date`` for events whose ``current_status`` is pending or
        investigating.
    """
    rows = (
        db.query(SecurityEvent)
        .filter(
            SecurityEvent.event_date < today,
            SecurityEvent.current_status.in_(["pending", "investigating"]),
        )
        .all()
    )
    return [
        {
            "match_key": r.match_key,
            "title": r.title,
            "star_rank": r.star_rank,
            "event_date": r.event_date.isoformat(),
        }
        for r in rows
    ]


def _upsert_event(db: Session, today: date, ev: dict) -> tuple[bool, bool]:
    """Insert a new SecurityEvent or extend the open one with the same match_key.

    Args:
        db: Active SQLAlchemy session.
        today: Date the merged event applies to.
        ev: Aggregated event dict from ``claude_pro.aggregate_daily``.

    Returns:
        Tuple ``(created, updated)``; exactly one of the booleans is True.
    """
    existing = (
        db.query(SecurityEvent)
        .filter(
            SecurityEvent.match_key == ev["match_key"],
            SecurityEvent.current_status.in_(["pending", "investigating"]),
        )
        .order_by(SecurityEvent.event_date.desc())
        .first()
    )
    if existing:
        existing.date_end = today
        existing.detection_count = (existing.detection_count or 0) + ev.get(
            "detection_count", 1
        )
        # Refresh Sonnet-produced fields so 新【分析依據】、新 suggests、重新分析的標題/風險評估
        # 都會反映到既有 row（current_status 與 created_at 保留 DB metadata）
        existing.star_rank = ev["star_rank"]
        existing.title = ev["title"]
        existing.description = ev.get("description")
        existing.affected_summary = ev["affected_summary"]
        existing.affected_detail = ev.get("affected_detail")
        existing.suggests = ev.get("suggests")
        existing.ioc_list = ev.get("ioc_list")
        existing.mitre_tags = ev.get("mitre_tags")
        existing.updated_at = datetime.now(timezone.utc)
        return False, True

    db.add(
        SecurityEvent(
            event_date=today,
            star_rank=ev["star_rank"],
            title=ev["title"],
            description=ev.get("description"),
            affected_summary=ev["affected_summary"],
            affected_detail=ev.get("affected_detail"),
            match_key=ev["match_key"],
            detection_count=ev.get("detection_count", 1),
            suggests=ev.get("suggests"),
            ioc_list=ev.get("ioc_list"),
            mitre_tags=ev.get("mitre_tags"),
            current_status="pending",
        )
    )
    return True, False


def run_pro_task(
    *,
    today: date | None = None,
    anthropic_client_factory: Callable,
    db_factory: Callable[[], Session],
) -> None:
    """Execute one Sonnet daily aggregation cycle.

    Reads ``scheduler.get_runtime()`` to decide whether the cycle should run.
    When ``is_enabled`` is False the function returns immediately without any
    Anthropic or DB I/O. Otherwise it collects today's done ChunkResult rows,
    groups events by ``match_key``, asks Claude Sonnet to merge them against
    yesterday's still-open SecurityEvents, then upserts the merged results
    into ``tb_security_events`` and records one ``tb_daily_analysis`` row.

    Args:
        today: Override the analysis date (defaults to UTC today). Useful for
            tests and replay runs.
        anthropic_client_factory: Callable returning an Anthropic client.
        db_factory: Callable returning a SQLAlchemy ``Session``. The session
            is committed but not closed; lifecycle is the caller's
            responsibility.

    Returns:
        None. All output is written to ``tb_daily_analysis`` and
        ``tb_security_events`` via ``db_factory``.
    """
    rt = scheduler.get_runtime()
    if not rt.is_enabled:
        logger.info("pro_task: skipped (is_enabled=False)")
        return

    today = today or datetime.now(timezone.utc).date()
    db = db_factory()

    da = DailyAnalysis(
        analysis_date=today,
        status="processing",
        started_at=datetime.now(timezone.utc),
    )
    db.add(da)
    try:
        db.commit()
        db.refresh(da)
    except Exception:
        db.rollback()
        da = db.query(DailyAnalysis).filter_by(analysis_date=today).one()

    try:
        grouped = _collect_today_events(db, today)
        da.chunk_results_count = sum(len(v) for v in grouped.values())
        if not grouped:
            da.status = "done"
            da.events_created = 0
            da.events_updated = 0
            da.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"pro_task: no chunks for {today}")
            return

        prev = _recent_open_events_for_continuity(db, today)
        ant = anthropic_client_factory()
        merged = claude_pro.aggregate_daily(
            grouped_events=grouped,
            previous_events=prev,
            today=today.isoformat(),
            client=ant,
            db=db,
        )

        created = updated = 0
        for ev in merged:
            c, u = _upsert_event(db, today, ev)
            created += int(c)
            updated += int(u)

        da.events_created = created
        da.events_updated = updated
        da.status = "done"
        da.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("pro_task: date=%s created=%d updated=%d", today, created, updated)
    except Exception as exc:
        db.rollback()
        da.status = "failed"
        da.error_message = str(exc)
        da.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.exception("pro_task: failed — %s", exc)
