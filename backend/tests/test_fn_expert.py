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

from app.db.models.analysis import ChunkResult, DailyAnalysis, LogBatch
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
    ChunkResult.__table__,
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


def _seed_setting(
    engine,
    haiku_enabled: bool = False,
    sonnet_enabled: bool = False,
    haiku_interval_minutes: int = 30,
) -> None:
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    setting = ExpertSetting(
        id=1,
        haiku_enabled=haiku_enabled,
        haiku_interval_minutes=haiku_interval_minutes,
        sonnet_enabled=sonnet_enabled,
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


def test_trigger_401_not_logged_in(client):
    """對應 T-AT-06"""
    resp = client.post("/expert/analysis/trigger")
    assert resp.status_code == 401


def test_trigger_403_no_permission(client, engine):
    """對應 T-AT-07"""
    user_id = _setup_plain_user(engine, "noperm1@test.com")
    _seed_setting(engine, sonnet_enabled=False)

    body = {"time_from": "2026-05-14T00:00:00Z", "time_to": "2026-05-14T10:00:00Z"}
    resp = client.post(
        "/expert/analysis/trigger", json=body, headers=_auth_headers(user_id)
    )

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 新行為測試：純 Sonnet + time_from/time_to (Task 8)
# ---------------------------------------------------------------------------


def test_trigger_analysis_returns_202_with_time_range(client, engine):
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine, sonnet_enabled=False)  # 不影響手動觸發

    body = {"time_from": "2026-05-14T00:00:00Z", "time_to": "2026-05-14T10:00:00Z"}

    with patch("app.api.fn_expert._dispatch_sonnet_job") as mock_sonnet:
        resp = client.post(
            "/expert/analysis/trigger", json=body, headers=_auth_headers(user_id)
        )

    assert resp.status_code == 202
    assert resp.json()["message"] == "分析已啟動"
    mock_sonnet.assert_called_once()
    call_kwargs = mock_sonnet.call_args.kwargs
    assert "time_from" in call_kwargs
    assert "time_to" in call_kwargs


def test_trigger_analysis_409_when_sonnet_running(client, engine):
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine)
    _seed_daily_analysis(engine, status="processing")

    body = {"time_from": "2026-05-14T00:00:00Z", "time_to": "2026-05-14T10:00:00Z"}
    resp = client.post(
        "/expert/analysis/trigger", json=body, headers=_auth_headers(user_id)
    )

    assert resp.status_code == 409


def test_trigger_analysis_not_blocked_by_haiku_running(client, engine):
    """互鎖規則：Haiku 跑時 Sonnet 仍可觸發。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine)
    _seed_log_batch(engine, status="running")

    body = {"time_from": "2026-05-14T00:00:00Z", "time_to": "2026-05-14T10:00:00Z"}
    with patch("app.api.fn_expert._dispatch_sonnet_job"):
        resp = client.post(
            "/expert/analysis/trigger", json=body, headers=_auth_headers(user_id)
        )

    assert resp.status_code == 202


# ---------------------------------------------------------------------------
# GET /expert/analysis/status tests
# ---------------------------------------------------------------------------


def test_status_returns_haiku_and_sonnet_sections(client, engine):
    """新 status response 應分 haiku / sonnet 兩段。"""
    user_id, _ = _setup_expert_user(engine)

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "haiku" in data
    assert "sonnet" in data
    assert "status" in data["haiku"]
    assert "status" in data["sonnet"]


def test_status_haiku_running_when_log_batch_running(client, engine):
    user_id, _ = _setup_expert_user(engine)
    _seed_log_batch(engine, status="running")

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))
    data = resp.json()["data"]
    assert data["haiku"]["status"] == "running"
    assert data["sonnet"]["status"] == "idle"


def test_status_sonnet_running_when_daily_analysis_processing(client, engine):
    user_id, _ = _setup_expert_user(engine)
    _seed_daily_analysis(engine, status="processing")

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))
    data = resp.json()["data"]
    assert data["sonnet"]["status"] == "running"
    assert data["haiku"]["status"] == "idle"


def test_status_sonnet_success_with_events_created(client, engine):
    user_id, _ = _setup_expert_user(engine)
    _seed_daily_analysis(engine, status="done", events_created=5)

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))
    data = resp.json()["data"]
    assert data["sonnet"]["status"] == "success"
    assert data["sonnet"]["events_created"] == 5


def test_status_haiku_success_when_log_batch_done(client, engine):
    user_id, _ = _setup_expert_user(engine)
    _seed_log_batch(engine, status="done")

    resp = client.get("/expert/analysis/status", headers=_auth_headers(user_id))
    data = resp.json()["data"]
    assert data["haiku"]["status"] == "success"


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

        with patch("app.tasks.pro_task._collect_events_in_range") as mock_collect:
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

        with patch("app.tasks.pro_task._collect_events_in_range") as mock_collect:
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
        with patch("app.tasks.pro_task._collect_events_in_range") as mock_collect:
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


def test_haiku_task_runs_regardless_of_is_enabled(db_session):
    """haiku_task 不再讀 is_enabled —— 排程開關由 scheduler 層控制。"""
    from datetime import datetime, timezone
    from app.tasks.haiku_task import run_haiku_task

    with patch("app.tasks.haiku_task.scheduler") as mock_sched:
        rt = MagicMock()
        rt.is_enabled = False
        rt.ssb_host = "https://x"
        rt.ssb_port = 443
        rt.ssb_logspace = "c"
        rt.ssb_username = "u"
        rt.ssb_password = "p"
        mock_sched.get_runtime.return_value = rt

        mock_ssb = MagicMock()
        mock_ssb.fetch_logs.return_value = []

        with patch("app.tasks.haiku_task.log_preaggregator") as mock_preagg:
            mock_preagg.preaggregate.return_value = ([], [])
            run_haiku_task(
                ssb_client_factory=lambda **kw: mock_ssb,
                anthropic_client_factory=lambda **kw: MagicMock(),
                db_factory=lambda: db_session,
                time_from=datetime(2026, 5, 14, 0, 0, tzinfo=timezone.utc),
                time_to=datetime(2026, 5, 14, 1, 0, tzinfo=timezone.utc),
            )

    mock_ssb.fetch_logs.assert_called_once()


def test_run_pro_task_filters_chunks_by_time_range(db_session):
    """run_pro_task 應只彙整 LogBatch.time_to 落在 time_from~time_to 區間的 chunks。"""
    from datetime import datetime, timezone
    from app.db.models.analysis import ChunkResult, LogBatch
    from app.tasks.pro_task import run_pro_task

    in_range = LogBatch(
        time_from=datetime(2026, 5, 14, 8, 0, tzinfo=timezone.utc),
        time_to=datetime(2026, 5, 14, 10, 0, tzinfo=timezone.utc),
        status="done",
        records_fetched=0,
        chunks_total=1,
        chunks_done=1,
    )
    out_of_range = LogBatch(
        time_from=datetime(2026, 5, 13, 8, 0, tzinfo=timezone.utc),
        time_to=datetime(2026, 5, 13, 10, 0, tzinfo=timezone.utc),
        status="done",
        records_fetched=0,
        chunks_total=1,
        chunks_done=1,
    )
    db_session.add_all([in_range, out_of_range])
    db_session.flush()
    db_session.add_all(
        [
            ChunkResult(
                batch_id=in_range.id,
                chunk_index=0,
                chunk_size=1,
                status="done",
                events=[
                    {
                        "match_key": "k1",
                        "star_rank": 3,
                        "title": "t",
                        "affected_summary": "a",
                        "affected_detail": "d",
                    }
                ],
            ),
            ChunkResult(
                batch_id=out_of_range.id,
                chunk_index=0,
                chunk_size=1,
                status="done",
                events=[
                    {
                        "match_key": "skip",
                        "star_rank": 3,
                        "title": "skip",
                        "affected_summary": "x",
                        "affected_detail": "x",
                    }
                ],
            ),
        ]
    )
    db_session.commit()

    with patch("app.tasks.pro_task.scheduler") as mock_sched:
        rt = MagicMock()
        rt.is_enabled = True
        mock_sched.get_runtime.return_value = rt

        with patch("app.tasks.pro_task.claude_pro.aggregate_daily") as mock_agg:
            mock_agg.return_value = []
            run_pro_task(
                anthropic_client_factory=lambda: MagicMock(),
                db_factory=lambda: db_session,
                manual_mode=True,
                time_from=datetime(2026, 5, 14, 0, 0, tzinfo=timezone.utc),
                time_to=datetime(2026, 5, 14, 23, 59, tzinfo=timezone.utc),
            )
            grouped = mock_agg.call_args.kwargs["grouped_events"]
            assert "k1" in grouped
            assert "skip" not in grouped


# ---------------------------------------------------------------------------
# POST /expert/log/trigger tests (Task 7)
# ---------------------------------------------------------------------------


def test_log_trigger_returns_202_starts_haiku(client, engine):
    """POST /expert/log/trigger 應同步寫 LogBatch running、投遞 Haiku job。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine, haiku_enabled=False)  # 手動觸發跟排程開關無關

    body = {
        "time_from": "2026-05-14T00:00:00Z",
        "time_to": "2026-05-14T10:00:00Z",
    }

    with patch("app.api.fn_expert._dispatch_haiku_job") as mock_haiku:
        resp = client.post(
            "/expert/log/trigger", json=body, headers=_auth_headers(user_id)
        )

    assert resp.status_code == 202
    assert resp.json()["message"] == "已啟動抓 log"
    mock_haiku.assert_called_once()


def test_log_trigger_409_when_running_overlap(client, engine):
    """重疊到 running batch → 409 overlap_type=running，不可繞過。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine)
    # _seed_log_batch 預設 time_from=2026-05-13、time_to=now，會與下方 body 重疊
    _seed_log_batch(engine, status="running")

    body = {"time_from": "2026-05-14T00:00:00Z", "time_to": "2026-05-14T10:00:00Z"}
    resp = client.post("/expert/log/trigger", json=body, headers=_auth_headers(user_id))

    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["message"] == "抓 log 進行中，請稍後再試"
    assert detail["overlap_type"] == "running"


def test_log_trigger_409_running_overlap_force_does_not_bypass(client, engine):
    """running 重疊 + force=true 仍 409（不能蓋進行中的）。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine)
    _seed_log_batch(engine, status="running")

    body = {
        "time_from": "2026-05-14T00:00:00Z",
        "time_to": "2026-05-14T10:00:00Z",
        "force": True,
    }
    resp = client.post("/expert/log/trigger", json=body, headers=_auth_headers(user_id))

    assert resp.status_code == 409
    assert resp.json()["detail"]["overlap_type"] == "running"


def _make_done_batch(engine, time_from_str: str, time_to_str: str) -> int:
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    # 用 naive UTC 寫入 DB，對齊 endpoint 內部 _strip_tz 後的比較格式（SQLite 用字串存 datetime，aware/naive 不能互比）
    batch = LogBatch(
        time_from=datetime.fromisoformat(time_from_str.replace("Z", "+00:00"))
        .astimezone(timezone.utc)
        .replace(tzinfo=None),
        time_to=datetime.fromisoformat(time_to_str.replace("Z", "+00:00"))
        .astimezone(timezone.utc)
        .replace(tzinfo=None),
        status="done",
        records_fetched=0,
        chunks_total=0,
        chunks_done=0,
    )
    db.add(batch)
    db.commit()
    batch_id = batch.id
    db.close()
    return batch_id


def _seed_chunk(engine, batch_id: int) -> int:
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    chunk = ChunkResult(
        batch_id=batch_id,
        chunk_index=0,
        chunk_size=10,
        events=[],
        status="done",
    )
    db.add(chunk)
    db.commit()
    chunk_id = chunk.id
    db.close()
    return chunk_id


def test_log_trigger_new_range_fully_covers_old_deletes_old(client, engine):
    """新範圍涵蓋舊範圍 → 自動刪舊建新（A 路徑，不需要 force）。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine)
    old_batch_id = _make_done_batch(
        engine, "2026-05-13T08:00:00Z", "2026-05-13T09:00:00Z"
    )
    _seed_chunk(engine, old_batch_id)

    body = {
        "time_from": "2026-05-13T07:00:00Z",  # 涵蓋 08:00-09:00
        "time_to": "2026-05-13T10:00:00Z",
    }
    with patch("app.api.fn_expert._dispatch_haiku_job"):
        resp = client.post(
            "/expert/log/trigger", json=body, headers=_auth_headers(user_id)
        )

    assert resp.status_code == 202

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    # SQLite auto-increment 會重用 id，不能直接查 old_batch_id；改用 time_from 確認剩下的是新 batch
    batches = db.query(LogBatch).order_by(LogBatch.id.desc()).all()
    assert len(batches) == 1
    assert batches[0].time_from.replace(tzinfo=None) == datetime(2026, 5, 13, 7, 0, 0)
    # 舊 batch 的 chunks 也應該被刪（用 time_from=08:00 區段的紀錄唯一識別舊狀態）
    assert (
        db.query(ChunkResult).filter(ChunkResult.batch_id == old_batch_id).count() == 0
    )
    db.close()


def test_log_trigger_409_partial_overlap_without_force(client, engine):
    """部分重疊 + force=false → 409 overlap_type=partial，附舊 batch 資訊。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine)
    old_batch_id = _make_done_batch(
        engine, "2026-05-13T08:00:00Z", "2026-05-13T09:00:00Z"
    )

    body = {
        "time_from": "2026-05-13T08:30:00Z",  # 在舊範圍內 = partial
        "time_to": "2026-05-13T09:30:00Z",
    }
    resp = client.post("/expert/log/trigger", json=body, headers=_auth_headers(user_id))

    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["overlap_type"] == "partial"
    assert len(detail["overlapping_batches"]) == 1
    assert detail["overlapping_batches"][0]["id"] == old_batch_id


def test_log_trigger_partial_overlap_with_force_deletes_and_creates(client, engine):
    """部分重疊 + force=true → 刪舊建新（D 路徑）。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine)
    old_batch_id = _make_done_batch(
        engine, "2026-05-13T08:00:00Z", "2026-05-13T09:00:00Z"
    )
    _seed_chunk(engine, old_batch_id)

    body = {
        "time_from": "2026-05-13T08:30:00Z",
        "time_to": "2026-05-13T09:30:00Z",
        "force": True,
    }
    with patch("app.api.fn_expert._dispatch_haiku_job"):
        resp = client.post(
            "/expert/log/trigger", json=body, headers=_auth_headers(user_id)
        )

    assert resp.status_code == 202

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    # 同 covers 測試：SQLite id 會重用，改用 time_from 確認剩下的是新 batch
    batches = db.query(LogBatch).all()
    assert len(batches) == 1
    assert batches[0].time_from.replace(tzinfo=None) == datetime(2026, 5, 13, 8, 30, 0)
    assert (
        db.query(ChunkResult).filter(ChunkResult.batch_id == old_batch_id).count() == 0
    )
    db.close()


def test_log_trigger_no_overlap_creates_directly(client, engine):
    """完全無重疊 → 202，舊 batch 保留不動。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine)
    old_batch_id = _make_done_batch(
        engine, "2026-05-13T08:00:00Z", "2026-05-13T09:00:00Z"
    )

    body = {
        "time_from": "2026-05-13T10:00:00Z",  # 完全在舊範圍之後
        "time_to": "2026-05-13T11:00:00Z",
    }
    with patch("app.api.fn_expert._dispatch_haiku_job"):
        resp = client.post(
            "/expert/log/trigger", json=body, headers=_auth_headers(user_id)
        )

    assert resp.status_code == 202

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    # 舊 batch 保留
    assert db.query(LogBatch).filter(LogBatch.id == old_batch_id).first() is not None
    db.close()


def test_log_trigger_401_not_logged_in(client):
    body = {"time_from": "2026-05-14T00:00:00Z", "time_to": "2026-05-14T10:00:00Z"}
    resp = client.post("/expert/log/trigger", json=body)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Phase 4 Task 9 — dispatch helper 拆 sonnet/haiku
# ---------------------------------------------------------------------------


def test_dispatch_sonnet_passes_time_range_to_pro_task(client, engine):
    """_dispatch_sonnet_job 該把 time_from/time_to forward 給 run_pro_task。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine)

    body = {"time_from": "2026-05-14T00:00:00Z", "time_to": "2026-05-14T10:00:00Z"}
    with patch("app.tasks.pro_task.run_pro_task") as mock_pro:
        from app import scheduler as sched_mod

        sched_mod._scheduler = None  # 強制走 fallback thread

        resp = client.post(
            "/expert/analysis/trigger", json=body, headers=_auth_headers(user_id)
        )
        import time

        for _ in range(50):
            if mock_pro.called:
                break
            time.sleep(0.02)

    assert resp.status_code == 202
    assert mock_pro.called
    pro_kwargs = mock_pro.call_args.kwargs
    assert pro_kwargs.get("manual_mode") is True
    assert pro_kwargs.get("time_from") is not None
    assert pro_kwargs.get("time_to") is not None


def test_dispatch_haiku_does_not_chain_sonnet_anymore(client, engine):
    """_dispatch_haiku_job 不再串接 sonnet（解耦後是兩件事）。"""
    user_id, _ = _setup_expert_user(engine)
    _seed_setting(engine)

    body = {"time_from": "2026-05-14T00:00:00Z", "time_to": "2026-05-14T10:00:00Z"}
    with (
        patch("app.tasks.haiku_task.run_haiku_task") as mock_haiku,
        patch("app.tasks.pro_task.run_pro_task") as mock_pro,
    ):
        from app import scheduler as sched_mod

        sched_mod._scheduler = None

        client.post("/expert/log/trigger", json=body, headers=_auth_headers(user_id))
        import time

        for _ in range(50):
            if mock_haiku.called:
                break
            time.sleep(0.02)

    assert mock_haiku.called
    import time

    time.sleep(0.1)
    assert not mock_pro.called, "Haiku 不該再串接 Sonnet"
