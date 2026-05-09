"""APScheduler integration — owns the BackgroundScheduler and runtime config cache."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config.settings import settings
from app.logger_utils.log_channels import get_system_logger

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
    """Stub — Task 5 implements; needed here so the job can be registered."""
    pass


def _haiku_job() -> None:
    """Stub — Task 6 implements."""
    pass


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
