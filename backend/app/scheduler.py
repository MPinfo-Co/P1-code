"""APScheduler integration — owns the BackgroundScheduler and runtime config cache."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config.settings import settings
from app.db.connector import SessionLocal
from app.db.models.fn_expert_setting import ExpertSetting
from app.logger_utils.log_channels import get_system_logger
from app.utils.crypto import decrypt

logger = get_system_logger()


@dataclass
class RuntimeSettings:
    is_enabled: bool = False
    schedule_time: str | None = None
    ssb_host: str | None = None
    ssb_port: int = 443
    ssb_logspace: str | None = None
    ssb_username: str | None = None
    ssb_password: str | None = None
    last_loaded_at: datetime | None = None


_runtime: RuntimeSettings = RuntimeSettings()
_scheduler: BackgroundScheduler | None = None


def get_runtime() -> RuntimeSettings:
    """Return the current cached runtime settings."""
    return _runtime


def _sync_settings() -> None:
    """Reload `tb_expert_settings` (id=1) into the runtime cache.

    Reschedules the Sonnet job's CronTrigger when `schedule_time` changes.
    Safe no-op if the singleton row is missing.
    """
    global _runtime
    session = SessionLocal()
    try:
        row = session.get(ExpertSetting, 1)
        if row is None:
            logger.info("tb_expert_settings has no id=1 row; scheduler stays disabled")
            return
        new_rt = RuntimeSettings(
            is_enabled=bool(row.is_enabled),
            schedule_time=row.schedule_time,
            ssb_host=row.ssb_host,
            ssb_port=row.ssb_port or 443,
            ssb_logspace=row.ssb_logspace,
            ssb_username=row.ssb_username,
            ssb_password=decrypt(row.ssb_password_enc),
            last_loaded_at=datetime.utcnow(),
        )
    finally:
        session.close()

    prev_time = _runtime.schedule_time
    _runtime = new_rt

    if (
        _scheduler is not None
        and new_rt.schedule_time
        and new_rt.schedule_time != prev_time
    ):
        try:
            hh, mm = new_rt.schedule_time.split(":")
            _scheduler.reschedule_job(
                "sonnet_job",
                trigger=CronTrigger(hour=int(hh), minute=int(mm)),
            )
            logger.info("rescheduled sonnet_job to %s UTC daily", new_rt.schedule_time)
        except (ValueError, KeyError) as exc:
            logger.error("failed to reschedule sonnet_job: %s", exc)


def _haiku_job() -> None:
    """APScheduler entry point for the Haiku interval job.

    Wires the production factories into ``run_haiku_task``. Wrapped in a
    broad except so a single failed run never tears down the scheduler.
    """
    from anthropic import Anthropic

    from app.tasks.haiku_task import run_haiku_task
    from app.tasks.ssb_client import SSBClient

    try:
        run_haiku_task(
            ssb_client_factory=lambda **kw: SSBClient(**kw),
            anthropic_client_factory=lambda **kw: Anthropic(**kw),
            db_factory=SessionLocal,
        )
    except Exception:
        logger.exception("haiku_job failed")


def _sonnet_job() -> None:
    """Stub — Task 7 implements."""
    pass


def start_scheduler() -> None:
    """Start the BackgroundScheduler and register all periodic jobs."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        logger.warning("scheduler already running, skipping start")
        return
    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(
        _sync_settings,
        IntervalTrigger(minutes=settings.expert_settings_reload_minutes),
        id="settings_sync",
        next_run_time=datetime.utcnow(),
    )
    sched.add_job(
        _haiku_job,
        IntervalTrigger(minutes=settings.haiku_interval_minutes),
        id="haiku_job",
    )
    # Sonnet is added with a placeholder cron; rescheduled by _sync_settings once DB is read
    sched.add_job(_sonnet_job, CronTrigger(hour=0, minute=30), id="sonnet_job")
    sched.start()
    _scheduler = sched
    logger.info("scheduler started: jobs=%s", [j.id for j in sched.get_jobs()])


def stop_scheduler() -> None:
    """Shut down the BackgroundScheduler and clear the module-level reference."""
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    logger.info("scheduler stopped")
