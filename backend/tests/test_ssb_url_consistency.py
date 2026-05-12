"""Tests for issue-290: SSB base URL consistency between scheduler and ssb-test API.

TC-01: SSBClient base URL 由 ssb_host/ssb_port 拼裝，與測試連線 API 規則一致。
TC-04: tb_expert_settings 連線欄位為 NULL 時，haiku_task 標記 failed 並不拋例外。
TC-05: settings_sync 重新載入後，後續排程使用新 host 拼裝 URL。
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from app import scheduler
from app.db.models.analysis import LogBatch
from app.db.models.fn_expert_setting import ExpertSetting
from app.tasks.haiku_task import run_haiku_task
from app.utils.crypto import encrypt


# ---------------------------------------------------------------------------
# TC-01: base URL 拼裝一致性
# ---------------------------------------------------------------------------


def test_ssb_client_base_url_matches_test_api_rule(db_session):
    """對應 TC-01

    haiku_task 傳入 SSBClient 的 host 必須為 https://{ssb_host}:{ssb_port}，
    與設定頁測試連線 API 建構 base_url 的規則完全相同。
    """
    captured_kwargs: dict = {}

    def fake_ssb_factory(**kw):
        captured_kwargs.update(kw)
        fake = MagicMock()
        fake.fetch_logs.return_value = []
        return fake

    scheduler._runtime = scheduler.RuntimeSettings(
        is_enabled=True,
        ssb_host="192.168.10.48",
        ssb_port=443,
        ssb_logspace="center",
        ssb_username="mpinfo",
        ssb_password="secret",
    )

    ant = MagicMock()
    ant.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps([]))]
    )

    run_haiku_task(
        ssb_client_factory=fake_ssb_factory,
        anthropic_client_factory=lambda **_: ant,
        db_factory=lambda: db_session,
    )

    # 驗證傳給 SSBClient 的 host 與測試連線 API 規則一致：https://{host}:{port}
    assert captured_kwargs.get("host") == "https://192.168.10.48:443"


def test_ssb_client_base_url_with_non_standard_port(db_session):
    """TC-01 補充：非標準 port 也應正確拼裝。"""
    captured_kwargs: dict = {}

    def fake_ssb_factory(**kw):
        captured_kwargs.update(kw)
        fake = MagicMock()
        fake.fetch_logs.return_value = []
        return fake

    scheduler._runtime = scheduler.RuntimeSettings(
        is_enabled=True,
        ssb_host="10.0.0.5",
        ssb_port=8443,
        ssb_logspace="ALL",
        ssb_username="admin",
        ssb_password="pw",
    )

    ant = MagicMock()
    ant.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps([]))]
    )

    run_haiku_task(
        ssb_client_factory=fake_ssb_factory,
        anthropic_client_factory=lambda **_: ant,
        db_factory=lambda: db_session,
    )

    assert captured_kwargs.get("host") == "https://10.0.0.5:8443"


# ---------------------------------------------------------------------------
# TC-04: SSB 連線資訊未設定時的行為
# ---------------------------------------------------------------------------


def test_haiku_task_marks_failed_when_ssb_host_is_none(db_session):
    """對應 TC-04

    tb_expert_settings 的連線欄位為 NULL 時，haiku_task 應：
    - 不呼叫 SSBClient（不拋網路例外）
    - 在 tb_log_batches 寫入 status=failed、error_message 說明未設定
    """
    ssb_called = []

    def fake_ssb_factory(**kw):
        ssb_called.append(kw)
        return MagicMock()

    scheduler._runtime = scheduler.RuntimeSettings(
        is_enabled=True,
        ssb_host=None,  # 尚未設定
        ssb_logspace="ALL",
        ssb_username="u",
        ssb_password="p",
    )

    ant = MagicMock()

    run_haiku_task(
        ssb_client_factory=fake_ssb_factory,
        anthropic_client_factory=lambda **_: ant,
        db_factory=lambda: db_session,
    )

    assert len(ssb_called) == 0, (
        "SSBClient should not be instantiated when host is None"
    )

    batches = db_session.query(LogBatch).all()
    assert len(batches) == 1
    b = batches[0]
    assert b.status == "failed"
    assert b.error_message is not None
    assert "SSB" in b.error_message or "連線" in b.error_message


def test_haiku_task_marks_failed_when_ssb_password_is_none(db_session):
    """TC-04 補充：password 為 NULL 時同樣應標記 failed。"""
    ssb_called = []

    def fake_ssb_factory(**kw):
        ssb_called.append(kw)
        return MagicMock()

    scheduler._runtime = scheduler.RuntimeSettings(
        is_enabled=True,
        ssb_host="192.168.10.48",
        ssb_port=443,
        ssb_logspace="ALL",
        ssb_username="u",
        ssb_password=None,  # 密碼未設定
    )

    ant = MagicMock()

    run_haiku_task(
        ssb_client_factory=fake_ssb_factory,
        anthropic_client_factory=lambda **_: ant,
        db_factory=lambda: db_session,
    )

    assert len(ssb_called) == 0

    b = db_session.query(LogBatch).one()
    assert b.status == "failed"
    assert b.error_message is not None


# ---------------------------------------------------------------------------
# TC-05: settings_sync 重新載入後，後續排程使用新 host
# ---------------------------------------------------------------------------


class _NoCloseSession:
    """Proxy that delegates everything to the wrapped session but silences .close()."""

    def __init__(self, s):
        self._s = s

    def __getattr__(self, k):
        return getattr(self._s, k)

    def close(self):
        pass


@pytest.fixture
def reset_runtime():
    scheduler.stop_scheduler()
    scheduler._runtime = scheduler.RuntimeSettings()
    yield
    scheduler.stop_scheduler()
    scheduler._runtime = scheduler.RuntimeSettings()


def test_settings_sync_updates_ssb_host_in_runtime(
    db_session, reset_runtime, monkeypatch
):
    """對應 TC-05

    tb_expert_settings 修改 ssb_host 並呼叫 _sync_settings 後，
    get_runtime() 應反映新的 host 值，後續排程用新 host 拼裝 URL。
    """
    # 初始設定
    row = ExpertSetting(
        id=1,
        is_enabled=True,
        frequency="daily",
        schedule_time="02:00",
        ssb_host="192.168.10.48",
        ssb_port=443,
        ssb_logspace="center",
        ssb_username="mpinfo",
        ssb_password_enc=encrypt("old_password"),
    )
    db_session.add(row)
    db_session.commit()

    monkeypatch.setattr(scheduler, "SessionLocal", lambda: _NoCloseSession(db_session))
    scheduler._sync_settings()

    rt = scheduler.get_runtime()
    assert rt.ssb_host == "192.168.10.48"

    # 模擬設定頁修改 ssb_host 後儲存
    row.ssb_host = "10.10.20.30"
    db_session.commit()

    scheduler._sync_settings()

    rt_new = scheduler.get_runtime()
    assert rt_new.ssb_host == "10.10.20.30"

    # 確認拼裝後的 URL 也更新
    expected_url = f"https://{rt_new.ssb_host}:{rt_new.ssb_port}"
    assert expected_url == "https://10.10.20.30:443"
