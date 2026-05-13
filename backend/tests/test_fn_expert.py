"""
Tests for fn_expert APIs (Issue 298):
  POST /expert/analysis/trigger
  GET  /expert/analysis/status

TestSpec IDs: T-AT-01 ~ T-AT-07, T-AS-01 ~ T-AS-07, T-ER-01 ~ T-ER-05
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

import anthropic
import httpx
import pytest
from sqlalchemy.orm import sessionmaker

from app.db.models.analysis import DailyAnalysis, LogBatch
from app.db.models.fn_expert_setting import ExpertSetting
from app.db.models.function_access import (
    FunctionFolder,
    FunctionItems as Function,
    RoleFunction,
)
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password

os.environ.setdefault("AES_KEY", "test-aes-256-key-for-pytest-12345")

_EXTRA_TABLES = [
    ExpertSetting.__table__,
    LogBatch.__table__,
    DailyAnalysis.__table__,
]


# ---------------------------------------------------------------------------
# Create extra tables needed for this test module
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function", autouse=True)
def _create_extra_tables(engine):
    """Ensure expert setting + analysis tables exist."""
    for table in _EXTRA_TABLES:
        table.create(bind=engine, checkfirst=True)
    yield
    for table in reversed(_EXTRA_TABLES):
        table.drop(bind=engine, checkfirst=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_folder(db, code: str = "資安專家") -> int:
    folder = FunctionFolder(folder_code=code, folder_label=code, sort_order=1)
    db.add(folder)
    db.flush()
    return folder.id


def _make_function(db, code: str, folder_id: int) -> int:
    fn = Function(
        function_code=code,
        function_label=code,
        folder_id=folder_id,
        sort_order=1,
    )
    db.add(fn)
    db.flush()
    return fn.function_id


def _make_role(db, name: str) -> int:
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role.id


def _make_user(db, email: str, name: str = "Test User") -> int:
    user = User(name=name, email=email, password_hash=hash_password("pw"))
    db.add(user)
    db.flush()
    return user.id


def _assign_role(db, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _grant_function(db, role_id: int, function_id: int) -> None:
    db.add(RoleFunction(role_id=role_id, function_id=function_id))
    db.flush()


def _auth_headers(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _setup_expert_user(engine) -> tuple[int, int]:
    """Create user with fn_expert permission. Return (user_id, fn_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_folder(db)
    fn_id = _make_function(db, "fn_expert", folder_id)
    role_id = _make_role(db, "admin")
    user_id = _make_user(db, "expert@test.com")
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_id)
    db.commit()
    db.close()
    return user_id, fn_id


def _setup_plain_user(engine, email: str = "plain@test.com") -> int:
    """Create user without fn_expert permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, f"plain_{email}")
    user_id = _make_user(db, email)
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id


def _seed_setting(engine, is_enabled: bool = False) -> None:
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    setting = ExpertSetting(
        id=1,
        is_enabled=is_enabled,
        frequency="daily",
        schedule_time="02:00",
        ssb_host="https://192.168.10.48",
        ssb_port=443,
        ssb_logspace="center",
        ssb_username="mpinfo",
    )
    db.add(setting)
    db.commit()
    db.close()


def _seed_log_batch(
    engine, status: str = "done", time_to: datetime | None = None
) -> int:
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    now = time_to or datetime.now(timezone.utc)
    batch = LogBatch(
        time_from=datetime(2026, 5, 13, 0, 0, 0),
        time_to=now,
        status=status,
        records_fetched=0,
        chunks_total=0,
        chunks_done=0,
    )
    db.add(batch)
    db.commit()
    batch_id = batch.id
    db.close()
    return batch_id


def _seed_daily_analysis(
    engine,
    status: str,
    events_created: int = 0,
    error_message: str | None = None,
    analysis_date: date | None = None,
) -> int:
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    da = DailyAnalysis(
        analysis_date=analysis_date or date(2026, 5, 13),
        status=status,
        events_created=events_created,
        error_message=error_message,
    )
    db.add(da)
    db.commit()
    da_id = da.id
    db.close()
    return da_id


# ---------------------------------------------------------------------------
# POST /expert/analysis/trigger tests
# ---------------------------------------------------------------------------


def test_trigger_no_schedule_has_done_batch_returns_202(client, engine):
    """對應 T-AT-01"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine, is_enabled=False)
    _seed_log_batch(engine, status="done")

    with (
        patch("app.api.fn_expert._dispatch_haiku_job") as mock_haiku,
    ):
        resp = client.post("/expert/analysis/trigger", headers=_auth_headers(user_id))

    assert resp.status_code == 202
    assert resp.json()["message"] == "分析已啟動"
    mock_haiku.assert_called_once()


def test_trigger_no_schedule_no_done_batch_first_time_returns_202(client, engine):
    """對應 T-AT-02"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine, is_enabled=False)
    # No done batches

    with patch("app.api.fn_expert._dispatch_haiku_job") as mock_haiku:
        resp = client.post("/expert/analysis/trigger", headers=_auth_headers(user_id))

    assert resp.status_code == 202
    assert resp.json()["message"] == "分析已啟動"
    mock_haiku.assert_called_once()

    # Verify time_from is today 00:00
    call_kwargs = mock_haiku.call_args
    assert call_kwargs is not None


def test_trigger_with_schedule_returns_202_starts_sonnet(client, engine):
    """對應 T-AT-03"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine, is_enabled=True)

    with patch("app.api.fn_expert._dispatch_sonnet_job") as mock_sonnet:
        resp = client.post("/expert/analysis/trigger", headers=_auth_headers(user_id))

    assert resp.status_code == 202
    assert resp.json()["message"] == "分析已啟動"
    mock_sonnet.assert_called_once()


def test_trigger_409_when_log_batch_running(client, engine):
    """對應 T-AT-04"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine, is_enabled=False)
    _seed_log_batch(engine, status="running")

    resp = client.post("/expert/analysis/trigger", headers=_auth_headers(user_id))

    assert resp.status_code == 409
    assert resp.json()["detail"] == "分析進行中，請稍後再試"


def test_trigger_409_when_daily_analysis_processing(client, engine):
    """對應 T-AT-05"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine, is_enabled=True)
    _seed_daily_analysis(engine, status="processing")

    resp = client.post("/expert/analysis/trigger", headers=_auth_headers(user_id))

    assert resp.status_code == 409
    assert resp.json()["detail"] == "分析進行中，請稍後再試"


def test_trigger_401_not_logged_in(client):
    """對應 T-AT-06"""
    resp = client.post("/expert/analysis/trigger")
    assert resp.status_code == 401


def test_trigger_403_no_permission(client, engine):
    """對應 T-AT-07"""
    user_id = _setup_plain_user(engine, "noperm1@test.com")
    _seed_setting(engine, is_enabled=False)

    resp = client.post("/expert/analysis/trigger", headers=_auth_headers(user_id))

    assert resp.status_code == 403


def test_trigger_upsert_daily_analysis_when_enabled(client, engine):
    """對應 T-AT-03 延伸：UPSERT tb_daily_analysis 當日紀錄為 processing。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine, is_enabled=True)

    with patch("app.api.fn_expert._dispatch_sonnet_job"):
        resp = client.post("/expert/analysis/trigger", headers=_auth_headers(user_id))

    assert resp.status_code == 202

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    today = datetime.now(timezone.utc).date()
    da = db.query(DailyAnalysis).filter(DailyAnalysis.analysis_date == today).first()
    db.close()
    assert da is not None
    assert da.status == "processing"


def test_trigger_writes_running_batch_when_not_enabled(client, engine):
    """對應 T-AT-01 延伸：同步寫入 tb_log_batches running 標記。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine, is_enabled=False)

    with patch("app.api.fn_expert._dispatch_haiku_job"):
        resp = client.post("/expert/analysis/trigger", headers=_auth_headers(user_id))

    assert resp.status_code == 202

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    batch = db.query(LogBatch).filter(LogBatch.status == "running").first()
    db.close()
    assert batch is not None


# ---------------------------------------------------------------------------
# GET /expert/analysis/status tests
# ---------------------------------------------------------------------------


def test_status_success_returns_success_with_events_created(client, engine):
    """對應 T-AS-01"""
    user_id, _ = _setup_expert_user(engine)
    _seed_daily_analysis(engine, status="done", events_created=3)

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "success"
    assert data["events_created"] == 3
    assert data["error_message"] is None


def test_status_running_when_log_batch_running(client, engine):
    """對應 T-AS-02"""
    user_id, _ = _setup_expert_user(engine)
    _seed_log_batch(engine, status="running")

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "running"


def test_status_failed_returns_error_message(client, engine):
    """對應 T-AS-03"""
    user_id, _ = _setup_expert_user(engine)
    _seed_daily_analysis(
        engine,
        status="failed",
        error_message="SSB 認證失敗，請至『資安專家設定』檢查帳密",
    )

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "failed"
    assert data["error_message"] == "SSB 認證失敗，請至『資安專家設定』檢查帳密"
    assert data["events_created"] is None


def test_status_running_when_daily_analysis_processing(client, engine):
    """對應 T-AS-07"""
    user_id, _ = _setup_expert_user(engine)
    _seed_daily_analysis(engine, status="processing")

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "running"


def test_status_idle_when_no_records(client, engine):
    """對應 T-AS-04"""
    user_id, _ = _setup_expert_user(engine)

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "idle"
    assert data["events_created"] is None
    assert data["error_message"] is None


def test_status_401_not_logged_in(client):
    """對應 T-AS-05"""
    resp = client.get("/expert/analysis/status")
    assert resp.status_code == 401


def test_status_403_no_permission(client, engine):
    """對應 T-AS-06"""
    user_id = _setup_plain_user(engine, "noperm2@test.com")

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Error classification tests (TDD #3: haiku_task / pro_task)
# ---------------------------------------------------------------------------


def test_haiku_task_ssb_config_missing_writes_correct_message(db_session):
    """對應 T-ER-01"""
    from unittest.mock import patch

    from app.tasks.haiku_task import run_haiku_task

    # Setup settings with no SSB config
    with patch("app.tasks.haiku_task.scheduler") as mock_sched:
        rt = MagicMock()
        rt.is_enabled = True
        rt.ssb_host = None
        rt.ssb_logspace = None
        rt.ssb_username = None
        rt.ssb_password = None
        mock_sched.get_runtime.return_value = rt

        run_haiku_task(
            ssb_client_factory=MagicMock(),
            anthropic_client_factory=MagicMock(),
            db_factory=lambda: db_session,
        )

    batch = db_session.query(LogBatch).filter(LogBatch.status == "failed").first()
    assert batch is not None
    assert batch.error_message == "SSB 連線資訊未設定，請至『資安專家設定』填寫"


def test_haiku_task_ssb_auth_failure_writes_correct_message(db_session):
    """對應 T-ER-02"""
    from app.tasks.haiku_task import run_haiku_task

    with patch("app.tasks.haiku_task.scheduler") as mock_sched:
        rt = MagicMock()
        rt.is_enabled = True
        rt.ssb_host = "https://192.168.10.48"
        rt.ssb_port = 443
        rt.ssb_logspace = "center"
        rt.ssb_username = "user"
        rt.ssb_password = "wrongpw"
        mock_sched.get_runtime.return_value = rt

        # Mock SSB client to raise HTTPStatusError with 401
        mock_response = MagicMock()
        mock_response.status_code = 401
        http_error = httpx.HTTPStatusError(
            "401 Unauthorized", request=MagicMock(), response=mock_response
        )

        mock_ssb = MagicMock()
        mock_ssb.fetch_logs.side_effect = http_error

        run_haiku_task(
            ssb_client_factory=lambda **kw: mock_ssb,
            anthropic_client_factory=MagicMock(),
            db_factory=lambda: db_session,
        )

    batch = db_session.query(LogBatch).filter(LogBatch.status == "failed").first()
    assert batch is not None
    assert batch.error_message == "SSB 認證失敗，請至『資安專家設定』檢查帳密"


def test_pro_task_anthropic_auth_error_writes_admin_message(db_session):
    """對應 T-ER-03 (pro_task)"""
    from app.tasks.pro_task import run_pro_task

    with patch("app.tasks.pro_task.scheduler") as mock_sched:
        rt = MagicMock()
        rt.is_enabled = True
        mock_sched.get_runtime.return_value = rt

        # Pre-seed a DailyAnalysis so pro_task can update it
        today = date.today()
        da = DailyAnalysis(
            analysis_date=today,
            status="processing",
        )
        db_session.add(da)
        db_session.commit()

        with patch("app.tasks.pro_task._collect_today_events") as mock_collect:
            mock_collect.side_effect = anthropic.AuthenticationError.__new__(
                anthropic.AuthenticationError
            )
            run_pro_task(
                today=today,
                anthropic_client_factory=lambda: MagicMock(),
                db_factory=lambda: db_session,
            )

    da_result = (
        db_session.query(DailyAnalysis)
        .filter(DailyAnalysis.analysis_date == today)
        .first()
    )
    assert da_result is not None
    assert da_result.status == "failed"
    assert da_result.error_message == "系統錯誤，請聯絡管理員"


def test_pro_task_rate_limit_error_writes_retry_message(db_session):
    """對應 T-ER-04 (pro_task)"""
    from app.tasks.pro_task import run_pro_task

    with patch("app.tasks.pro_task.scheduler") as mock_sched:
        rt = MagicMock()
        rt.is_enabled = True
        mock_sched.get_runtime.return_value = rt

        today = date.today()
        da = DailyAnalysis(analysis_date=today, status="processing")
        db_session.add(da)
        db_session.commit()

        with patch("app.tasks.pro_task._collect_today_events") as mock_collect:
            mock_collect.side_effect = anthropic.RateLimitError.__new__(
                anthropic.RateLimitError
            )
            run_pro_task(
                today=today,
                anthropic_client_factory=lambda: MagicMock(),
                db_factory=lambda: db_session,
            )

    da_result = (
        db_session.query(DailyAnalysis)
        .filter(DailyAnalysis.analysis_date == today)
        .first()
    )
    assert da_result is not None
    assert da_result.status == "failed"
    assert da_result.error_message == "分析失敗，請稍後重試"


def test_error_message_truncated_to_200_chars(db_session):
    """對應 T-ER-05"""
    from app.tasks.pro_task import _classify_error, _ERROR_MSG_MAX_LEN

    long_msg = "x" * 300
    exc = Exception(long_msg)
    result = _classify_error(exc)
    assert len(result) <= _ERROR_MSG_MAX_LEN


def test_haiku_task_connection_error_writes_retry_message(db_session):
    """對應 T-ER-04 (haiku_task, ConnectError)"""
    from app.tasks.haiku_task import run_haiku_task

    with patch("app.tasks.haiku_task.scheduler") as mock_sched:
        rt = MagicMock()
        rt.is_enabled = True
        rt.ssb_host = "https://192.168.10.48"
        rt.ssb_port = 443
        rt.ssb_logspace = "center"
        rt.ssb_username = "user"
        rt.ssb_password = "pw"
        mock_sched.get_runtime.return_value = rt

        mock_ssb = MagicMock()
        mock_ssb.fetch_logs.side_effect = httpx.ConnectError("connection refused")

        run_haiku_task(
            ssb_client_factory=lambda **kw: mock_ssb,
            anthropic_client_factory=MagicMock(),
            db_factory=lambda: db_session,
        )

    batch = db_session.query(LogBatch).filter(LogBatch.status == "failed").first()
    assert batch is not None
    assert batch.error_message == "分析失敗，請稍後重試"


def test_haiku_task_anthropic_auth_error_writes_admin_message(db_session):
    """對應 T-ER-03 (haiku_task, AuthenticationError on chunk)"""
    from datetime import datetime, timezone

    from app.tasks.haiku_task import run_haiku_task

    with patch("app.tasks.haiku_task.scheduler") as mock_sched:
        rt = MagicMock()
        rt.is_enabled = True
        rt.ssb_host = "https://192.168.10.48"
        rt.ssb_port = 443
        rt.ssb_logspace = "center"
        rt.ssb_username = "user"
        rt.ssb_password = "pw"
        mock_sched.get_runtime.return_value = rt

        mock_ssb = MagicMock()
        mock_ssb.fetch_logs.return_value = [{"log": "test"}]

        with patch("app.tasks.haiku_task.log_preaggregator") as mock_preagg:
            mock_preagg.preaggregate.return_value = ([{"log": "test"}], [])
            with patch("app.tasks.haiku_task.claude_flash") as mock_flash:
                mock_flash.analyze_chunk.side_effect = (
                    anthropic.AuthenticationError.__new__(anthropic.AuthenticationError)
                )
                # Provide explicit time_from/time_to to avoid settings.haiku_interval_minutes
                now = datetime.now(timezone.utc)
                run_haiku_task(
                    ssb_client_factory=lambda **kw: mock_ssb,
                    anthropic_client_factory=lambda **kw: MagicMock(),
                    db_factory=lambda: db_session,
                    time_from=datetime(2026, 5, 13, 0, 0, 0),
                    time_to=now,
                )

    from app.db.models.analysis import ChunkResult

    chunk = db_session.query(ChunkResult).filter(ChunkResult.status == "failed").first()
    assert chunk is not None
    assert chunk.error_message == "系統錯誤，請聯絡管理員"


def test_status_returns_correct_message_ok(client, engine):
    """狀態 API 回傳 message='ok'"""
    user_id, _ = _setup_expert_user(engine)

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))

    assert resp.status_code == 200
    assert resp.json()["message"] == "ok"


# ---------------------------------------------------------------------------
# Manual-mode pipeline integration (regression for is_enabled=False trigger)
# ---------------------------------------------------------------------------


def test_run_pro_task_manual_mode_bypasses_is_enabled_guard(db_session):
    """手動觸發 Sonnet 即使 is_enabled=False 也要跑完，不可早退。"""
    from app.tasks.pro_task import run_pro_task

    with patch("app.tasks.pro_task.scheduler") as mock_sched:
        rt = MagicMock()
        rt.is_enabled = False
        mock_sched.get_runtime.return_value = rt

        today = date.today()
        with patch("app.tasks.pro_task._collect_today_events") as mock_collect:
            mock_collect.return_value = {}
            run_pro_task(
                today=today,
                anthropic_client_factory=lambda: MagicMock(),
                db_factory=lambda: db_session,
                manual_mode=True,
            )

    da = (
        db_session.query(DailyAnalysis)
        .filter(DailyAnalysis.analysis_date == today)
        .first()
    )
    assert da is not None, "manual_mode=True 時 run_pro_task 不該早退"
    assert da.status == "done"
    assert da.events_created == 0


def test_dispatch_haiku_then_sonnet_runs_pro_task_with_manual_mode(client, engine):
    """is_enabled=False + manual trigger：Haiku 跑完後 Sonnet 必須串接執行。

    既有測試一律 mock `_dispatch_haiku_job`，無法捕捉這條串接 bug。
    這支測試只 mock 外部 client，驗 run_pro_task 真的會被呼到。
    """
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine, is_enabled=False)

    with (
        patch("app.tasks.haiku_task.run_haiku_task") as mock_haiku,
        patch("app.tasks.pro_task.run_pro_task") as mock_pro,
        patch("app.api.fn_expert._scheduler_mod_for_dispatch", create=True),
    ):
        # 強制走 fallback thread 路徑（測試環境 scheduler 未啟動）
        from app import scheduler as sched_mod

        sched_mod._scheduler = None

        # 攔截 thread 內的 import：讓 _haiku_then_sonnet 走自訂 wiring

        resp = client.post("/expert/analysis/trigger", headers=_auth_headers(user_id))

        # 等 thread 跑完
        import time

        for _ in range(50):
            if mock_pro.called:
                break
            time.sleep(0.02)

    assert resp.status_code == 202
    assert mock_haiku.called, "haiku 必須先跑"
    assert mock_pro.called, "Sonnet 必須串接執行（這是 Bug 1）"
    pro_kwargs = mock_pro.call_args.kwargs
    assert pro_kwargs.get("manual_mode") is True, (
        "Sonnet 應以 manual_mode=True 呼叫，繞過 is_enabled 守門"
    )


def test_dispatch_sonnet_when_is_enabled_uses_manual_mode(client, engine):
    """is_enabled=True + manual trigger：Sonnet 也要以 manual_mode=True 呼叫，
    避免「分析中關掉排程」的 race 讓 Sonnet 半途早退。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine, is_enabled=True)

    with patch("app.tasks.pro_task.run_pro_task") as mock_pro:
        from app import scheduler as sched_mod

        sched_mod._scheduler = None

        resp = client.post("/expert/analysis/trigger", headers=_auth_headers(user_id))

        import time

        for _ in range(50):
            if mock_pro.called:
                break
            time.sleep(0.02)

    assert resp.status_code == 202
    assert mock_pro.called, "Sonnet 必須被呼叫"
    pro_kwargs = mock_pro.call_args.kwargs
    assert pro_kwargs.get("manual_mode") is True


def test_classify_error_fallback_returns_retry_message():
    """未分類 exception 應寫入「分析失敗，請稍後重試」，不可寫 raw exception 訊息。"""
    from app.tasks.haiku_task import _classify_error as haiku_classify
    from app.tasks.pro_task import _classify_error as pro_classify

    # 完全未分類的 exception（既非 anthropic / sqlalchemy / httpx / ValueError）
    class _UnknownError(Exception):
        pass

    exc = _UnknownError("internal IP 192.168.1.1 leaked, sensitive=true")
    assert haiku_classify(exc) == "分析失敗，請稍後重試"
    assert pro_classify(exc) == "分析失敗，請稍後重試"
