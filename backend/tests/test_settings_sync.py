"""Tests for _sync_settings: runtime reload from tb_expert_settings + Sonnet reschedule."""

import pytest

from app import scheduler
from app.db.models.fn_expert_setting import ExpertSetting
from app.utils.crypto import encrypt


class _NoCloseSession:
    """Proxy that delegates everything to the wrapped session but silences .close().

    _sync_settings calls session.close() in its finally block; without this
    wrapper the test session would be closed before assertions run.
    """

    def __init__(self, s):
        self._s = s

    def __getattr__(self, k):
        return getattr(self._s, k)

    def close(self):  # no-op
        pass


@pytest.fixture
def reset_runtime():
    """Reset module-level scheduler state before and after each test."""
    scheduler.stop_scheduler()
    scheduler._runtime = scheduler.RuntimeSettings()
    yield
    scheduler.stop_scheduler()
    scheduler._runtime = scheduler.RuntimeSettings()


@pytest.fixture
def expert_row(db_session):
    """Ensure id=1 row exists in tb_expert_settings; yield the ORM instance."""
    row = db_session.get(ExpertSetting, 1)
    if row is None:
        row = ExpertSetting(id=1, haiku_enabled=False, sonnet_enabled=False)
        db_session.add(row)
        db_session.commit()
    yield row


def test_sync_loads_is_enabled_and_decrypts_password(
    db_session, expert_row, reset_runtime, monkeypatch
):
    """_sync_settings must populate RuntimeSettings from the DB row and decrypt the password."""
    expert_row.haiku_enabled = True
    expert_row.sonnet_enabled = True
    expert_row.schedule_time = "02:30"
    expert_row.ssb_host = "https://192.168.10.48"
    expert_row.ssb_port = 443
    expert_row.ssb_logspace = "ALL"
    expert_row.ssb_username = "svc"
    expert_row.ssb_password_enc = encrypt("p@ss")
    db_session.commit()

    monkeypatch.setattr(scheduler, "SessionLocal", lambda: _NoCloseSession(db_session))
    scheduler._sync_settings()

    rt = scheduler.get_runtime()
    assert rt.haiku_enabled is True
    assert rt.sonnet_enabled is True
    assert rt.schedule_time == "02:30"
    assert rt.ssb_host == "https://192.168.10.48"
    assert rt.ssb_username == "svc"
    assert rt.ssb_password == "p@ss"
    assert rt.last_loaded_at is not None


def test_sync_reschedules_sonnet_when_schedule_time_changes(
    db_session, expert_row, reset_runtime, monkeypatch
):
    """When schedule_time changes, _sync_settings must reschedule sonnet_job."""
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: _NoCloseSession(db_session))
    scheduler.start_scheduler()
    try:
        expert_row.sonnet_enabled = True
        expert_row.schedule_time = "03:15"
        db_session.commit()

        scheduler._sync_settings()

        job = scheduler._scheduler.get_job("sonnet_job")
        fields = {f.name: str(f) for f in job.trigger.fields}
        assert fields["hour"] == "3"
        assert fields["minute"] == "15"
    finally:
        scheduler.stop_scheduler()


def test_sync_missing_row_does_not_crash(db_session, reset_runtime, monkeypatch):
    """When no id=1 row exists, _sync_settings returns silently without updating _runtime."""
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: _NoCloseSession(db_session))
    scheduler._sync_settings()

    rt = scheduler.get_runtime()
    assert rt.haiku_enabled is False
    assert rt.sonnet_enabled is False
    assert rt.last_loaded_at is None


def test_sync_none_schedule_time_does_not_reschedule(
    db_session, expert_row, reset_runtime, monkeypatch
):
    """When schedule_time is None, no reschedule attempt is made."""
    monkeypatch.setattr(scheduler, "SessionLocal", lambda: _NoCloseSession(db_session))
    scheduler.start_scheduler()
    try:
        expert_row.sonnet_enabled = True
        expert_row.schedule_time = None
        db_session.commit()

        # Capture placeholder trigger before sync
        job_before = scheduler._scheduler.get_job("sonnet_job")
        trigger_before = str(job_before.trigger)

        scheduler._sync_settings()

        job_after = scheduler._scheduler.get_job("sonnet_job")
        assert str(job_after.trigger) == trigger_before
    finally:
        scheduler.stop_scheduler()


def test_sync_loads_haiku_and_sonnet_enabled_independently(
    db_session, reset_runtime, monkeypatch
):
    """_sync_settings 應 reload 兩個 enabled flags。"""
    row = db_session.get(ExpertSetting, 1)
    if row is None:
        row = ExpertSetting(
            id=1,
            haiku_enabled=True,
            haiku_interval_minutes=15,
            sonnet_enabled=False,
            schedule_time="03:30",
            ssb_host="https://1.1.1.1",
            ssb_port=443,
            ssb_logspace="ls",
            ssb_username="u",
            ssb_password_enc=encrypt("p"),
        )
        db_session.add(row)
    else:
        row.haiku_enabled = True
        row.haiku_interval_minutes = 15
        row.sonnet_enabled = False
        row.schedule_time = "03:30"
        row.ssb_host = "https://1.1.1.1"
    db_session.commit()

    monkeypatch.setattr(scheduler, "SessionLocal", lambda: _NoCloseSession(db_session))
    scheduler._sync_settings()
    rt = scheduler.get_runtime()

    assert rt.haiku_enabled is True
    assert rt.haiku_interval_minutes == 15
    assert rt.sonnet_enabled is False
    assert rt.schedule_time == "03:30"
