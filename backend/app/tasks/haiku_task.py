"""Haiku Task — pull SSB logs, preaggregate, run Claude Haiku per chunk, persist.

Public entry: run_haiku_task(*, ssb_client_factory, anthropic_client_factory, db_factory,
                              time_from=None, time_to=None, batch_id=None)

The factory parameters keep the orchestrator unit-testable with fakes; production
wiring is done by app.scheduler._haiku_job.

When time_from / time_to / batch_id are supplied (manual trigger mode), the task
reuses the pre-created LogBatch row and uses the provided time window instead of
computing it from settings.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

import anthropic
import httpx
import sqlalchemy.exc

from app import scheduler
from app.config.settings import settings
from app.db.models.analysis import ChunkResult, LogBatch
from app.logger_utils.log_channels import get_system_logger
from app.tasks import claude_flash, log_preaggregator
from app.tasks.ssb_search import SSB_SEARCH_EXPRESSION

logger = get_system_logger()

_ERR_SSB_CONFIG = "SSB 連線資訊未設定，請至『資安專家設定』填寫"
_ERR_SSB_AUTH = "SSB 認證失敗，請至『資安專家設定』檢查帳密"
_ERR_ADMIN = "系統錯誤，請聯絡管理員"
_ERR_RETRY = "分析失敗，請稍後重試"
_ERROR_MSG_MAX_LEN = 200


def _classify_error(exc: BaseException) -> str:
    """Classify an exception into one of the 4 error buckets.

    Returns the user-facing error message (<= 200 chars).
    """
    if isinstance(
        exc, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)
    ):
        return _ERR_ADMIN
    if isinstance(exc, sqlalchemy.exc.SQLAlchemyError):
        return _ERR_ADMIN
    if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
        return _ERR_RETRY
    if isinstance(exc, anthropic.RateLimitError):
        return _ERR_RETRY
    if isinstance(exc, anthropic.APIStatusError):
        return _ERR_RETRY
    if isinstance(exc, (ValueError, KeyError)):
        # JSON parsing error
        return _ERR_RETRY
    return _ERR_RETRY


def run_haiku_task(
    *,
    ssb_client_factory: Callable,
    anthropic_client_factory: Callable,
    db_factory: Callable,
    time_from: datetime | None = None,
    time_to: datetime | None = None,
    batch_id: int | None = None,
) -> None:
    """Execute one Haiku analysis cycle.

    Args:
        ssb_client_factory: Builds an SSB client; called with host/logspace/username/password.
        anthropic_client_factory: Builds an Anthropic client; called with api_key.
        db_factory: Returns a SQLAlchemy Session.
        time_from: Override query window start (manual trigger mode).
        time_to: Override query window end (manual trigger mode).
        batch_id: Pre-created LogBatch id (manual trigger mode).
    """
    rt = scheduler.get_runtime()

    # TC-04: SSB connection info missing — record failure and exit early
    if (
        not rt.ssb_host
        or not rt.ssb_logspace
        or not rt.ssb_username
        or not rt.ssb_password
    ):
        db = db_factory()
        _time_to = time_to or datetime.utcnow()
        _time_from = time_from or (
            _time_to - timedelta(minutes=settings.haiku_interval_minutes)
        )
        if batch_id is not None:
            batch = db.get(LogBatch, batch_id)
            if batch is not None:
                batch.status = "failed"
                batch.error_message = _ERR_SSB_CONFIG
                db.commit()
        else:
            batch = LogBatch(
                time_from=_time_from,
                time_to=_time_to,
                status="failed",
                records_fetched=0,
                chunks_total=0,
                chunks_done=0,
                error_message=_ERR_SSB_CONFIG,
            )
            db.add(batch)
            db.commit()
        logger.warning("haiku_task: SSB connection info missing, skipping")
        return

    _time_to = time_to or datetime.utcnow()
    _time_from = time_from or (
        _time_to - timedelta(minutes=settings.haiku_interval_minutes)
    )

    # TC-01: base URL assembled from ssb_host/ssb_port
    ssb_base_url = f"{rt.ssb_host}:{rt.ssb_port}"

    db = db_factory()

    # Reuse pre-created batch or create new one
    if batch_id is not None:
        batch = db.get(LogBatch, batch_id)
        if batch is None:
            batch = LogBatch(
                time_from=_time_from,
                time_to=_time_to,
                status="running",
                records_fetched=0,
                chunks_total=0,
                chunks_done=0,
            )
            db.add(batch)
            db.flush()
    else:
        batch = LogBatch(
            time_from=_time_from,
            time_to=_time_to,
            status="running",
            records_fetched=0,
            chunks_total=0,
            chunks_done=0,
        )
        db.add(batch)
        db.flush()

    try:
        ssb = ssb_client_factory(
            host=ssb_base_url,
            logspace=rt.ssb_logspace,
            username=rt.ssb_username,
            password=rt.ssb_password,
        )
        raw_logs = ssb.fetch_logs(
            time_from=_time_from,
            time_to=_time_to,
            search_expression=SSB_SEARCH_EXPRESSION,
        )
    except httpx.HTTPStatusError as exc:
        logger.exception("haiku_task: SSB HTTP error")
        status_code = exc.response.status_code if exc.response is not None else None
        err_msg = _ERR_SSB_AUTH if status_code == 401 else _ERR_RETRY
        batch.status = "failed"
        batch.error_message = err_msg
        db.commit()
        return
    except httpx.TransportError:
        logger.exception("haiku_task: SSB connection error")
        batch.status = "failed"
        batch.error_message = _ERR_RETRY
        db.commit()
        return
    except anthropic.AuthenticationError:
        logger.exception("haiku_task: Anthropic auth error")
        batch.status = "failed"
        batch.error_message = _ERR_ADMIN
        db.commit()
        return
    except anthropic.PermissionDeniedError:
        logger.exception("haiku_task: Anthropic permission error")
        batch.status = "failed"
        batch.error_message = _ERR_ADMIN
        db.commit()
        return
    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception("haiku_task: DB error during SSB fetch")
        batch.status = "failed"
        batch.error_message = _ERR_ADMIN
        try:
            db.commit()
        except Exception:
            db.rollback()
        return
    except Exception as exc:
        logger.exception("haiku_task: unexpected error during SSB fetch")
        batch.status = "failed"
        batch.error_message = _classify_error(exc)
        db.commit()
        return

    forti, others = log_preaggregator.preaggregate(raw_logs)
    items = forti + others
    chunk_size = settings.haiku_chunk_size
    chunks = [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]
    logger.info(f"Retrieving {str(len(chunks))} chunks")

    batch.records_fetched = len(raw_logs)
    batch.chunks_total = len(chunks)
    batch.chunks_done = 0

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
        except anthropic.AuthenticationError:
            logger.exception(f"haiku_task: chunk {idx} auth error")
            db.add(
                ChunkResult(
                    batch_id=batch.id,
                    chunk_index=idx,
                    chunk_size=len(chunk),
                    events=[],
                    status="failed",
                    error_message=_ERR_ADMIN,
                )
            )
        except anthropic.PermissionDeniedError:
            logger.exception(f"haiku_task: chunk {idx} permission error")
            db.add(
                ChunkResult(
                    batch_id=batch.id,
                    chunk_index=idx,
                    chunk_size=len(chunk),
                    events=[],
                    status="failed",
                    error_message=_ERR_ADMIN,
                )
            )
        except sqlalchemy.exc.SQLAlchemyError:
            logger.exception(f"haiku_task: chunk {idx} DB error")
            db.add(
                ChunkResult(
                    batch_id=batch.id,
                    chunk_index=idx,
                    chunk_size=len(chunk),
                    events=[],
                    status="failed",
                    error_message=_ERR_ADMIN,
                )
            )
        except anthropic.RateLimitError:
            logger.exception(f"haiku_task: chunk {idx} rate limit")
            db.add(
                ChunkResult(
                    batch_id=batch.id,
                    chunk_index=idx,
                    chunk_size=len(chunk),
                    events=[],
                    status="failed",
                    error_message=_ERR_RETRY,
                )
            )
        except anthropic.APIStatusError:
            logger.exception(f"haiku_task: chunk {idx} API status error")
            db.add(
                ChunkResult(
                    batch_id=batch.id,
                    chunk_index=idx,
                    chunk_size=len(chunk),
                    events=[],
                    status="failed",
                    error_message=_ERR_RETRY,
                )
            )
        except httpx.TransportError:
            logger.exception(f"haiku_task: chunk {idx} connection error")
            db.add(
                ChunkResult(
                    batch_id=batch.id,
                    chunk_index=idx,
                    chunk_size=len(chunk),
                    events=[],
                    status="failed",
                    error_message=_ERR_RETRY,
                )
            )
        except Exception as exc:
            logger.exception(f"haiku_task: chunk {idx} failed")
            db.add(
                ChunkResult(
                    batch_id=batch.id,
                    chunk_index=idx,
                    chunk_size=len(chunk),
                    events=[],
                    status="failed",
                    error_message=_classify_error(exc),
                )
            )

    batch.status = "done"
    db.commit()
    logger.info(
        f"haiku_task: batch_id={batch.id} records={batch.records_fetched} chunks={batch.chunks_done}/{batch.chunks_total}"
    )
