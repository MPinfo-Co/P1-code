"""Haiku Task — pull SSB logs, preaggregate, run Claude Haiku per chunk, persist.

Public entry: run_haiku_task(*, ssb_client_factory, anthropic_client_factory, db_factory)

The factory parameters keep the orchestrator unit-testable with fakes; production
wiring is done by app.scheduler._haiku_job.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

from app import scheduler
from app.config.settings import settings
from app.db.models.analysis import ChunkResult, LogBatch
from app.logger_utils.log_channels import get_system_logger
from app.tasks import claude_flash, log_preaggregator
from app.tasks.ssb_search import SSB_SEARCH_EXPRESSION

logger = get_system_logger()


def run_haiku_task(
    *,
    ssb_client_factory: Callable,
    anthropic_client_factory: Callable,
    db_factory: Callable,
) -> None:
    """Execute one Haiku analysis cycle.

    Args:
        ssb_client_factory: Builds an SSB client; called with host/logspace/username/password.
        anthropic_client_factory: Builds an Anthropic client; called with api_key.
        db_factory: Returns a SQLAlchemy Session.
    """
    rt = scheduler.get_runtime()
    if not rt.is_enabled:
        logger.info("haiku_task: skipped (is_enabled=False)")
        return

    # TC-04: 連線資訊未設定時記錄失敗並提早結束，不丟未捕捉例外
    if (
        not rt.ssb_host
        or not rt.ssb_logspace
        or not rt.ssb_username
        or not rt.ssb_password
    ):
        db = db_factory()
        time_to = datetime.utcnow()
        time_from = time_to - timedelta(minutes=settings.haiku_interval_minutes)
        batch = LogBatch(
            time_from=time_from,
            time_to=time_to,
            status="failed",
            records_fetched=0,
            chunks_total=0,
            chunks_done=0,
            error_message="SSB 連線資訊未設定",
        )
        db.add(batch)
        db.commit()
        logger.warning("haiku_task: SSB 連線資訊未設定，跳過本次執行")
        return

    time_to = datetime.utcnow()
    time_from = time_to - timedelta(minutes=settings.haiku_interval_minutes)

    # TC-01: base URL 由 ssb_host/ssb_port 拼裝，與測試連線 API 使用相同規則
    ssb_base_url = f"{rt.ssb_host}:{rt.ssb_port}"
    ssb = ssb_client_factory(
        host=ssb_base_url,
        logspace=rt.ssb_logspace,
        username=rt.ssb_username,
        password=rt.ssb_password,
    )
    raw_logs = ssb.fetch_logs(
        time_from=time_from,
        time_to=time_to,
        search_expression=SSB_SEARCH_EXPRESSION,
    )

    forti, others = log_preaggregator.preaggregate(raw_logs)
    items = forti + others
    chunk_size = settings.haiku_chunk_size
    chunks = [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
    logger.info(f"Retrieving {str(len(chunks))} chunks")

    db = db_factory()
    batch = LogBatch(
        time_from=time_from,
        time_to=time_to,
        status="running",
        records_fetched=len(raw_logs),
        chunks_total=len(chunks),
        chunks_done=0,
    )
    db.add(batch)
    db.flush()

    ant = anthropic_client_factory(api_key=settings.anthropic_api_key)
    for idx, chunk in enumerate(chunks):
        try:
            events = claude_flash.analyze_chunk(chunk, client=ant)
            db.add(
                ChunkResult(
                    batch_id=batch.id,
                    chunk_index=idx,
                    chunk_size=len(chunk),
                    events=events,
                    status="done",
                    processed_at=datetime.utcnow(),
                )
            )
            batch.chunks_done += 1
        except Exception as exc:
            logger.exception(f"haiku_task: chunk {idx} failed")
            db.add(
                ChunkResult(
                    batch_id=batch.id,
                    chunk_index=idx,
                    chunk_size=len(chunk),
                    events=[],
                    status="failed",
                    error_message=str(exc),
                )
            )

    batch.status = "done"
    db.commit()
    logger.info(
        f"haiku_task: batch_id={batch.id} records={batch.records_fetched} chunks={batch.chunks_done}/{batch.chunks_total}")
