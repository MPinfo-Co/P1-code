"""
Tests for fn_expert_setting APIs (Issue 211):
  GET    /expert/settings
  PUT    /expert/settings
  POST   /expert/ssb-test

ExpertSetting 採單例設計：tb_expert_settings 永遠只有 id=1 一筆紀錄。
TestSpec IDs: T1–T21
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import sessionmaker

from app.db.models.fn_expert_setting import ExpertSetting
from app.db.models.function_access import (
    FunctionItems as Function,
    FunctionFolder,
    RoleFunction,
)
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password

os.environ.setdefault("AES_KEY", "test-aes-256-key-for-pytest-12345")

SETTING_ID = 1
_EXPERT_TABLES = [ExpertSetting.__table__]


# ---------------------------------------------------------------------------
# Override engine fixture to also create expert_setting tables
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function", autouse=True)
def _create_expert_tables(engine):
    """Ensure tb_expert_settings exists in the test engine."""
    for table in _EXPERT_TABLES:
        table.create(bind=engine, checkfirst=True)
    yield
    for table in reversed(_EXPERT_TABLES):
        table.drop(bind=engine, checkfirst=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_function_folder(db, name: str = "資安專家", sort_order: int = 1) -> int:
    folder = FunctionFolder(folder_code=name, folder_label=name, sort_order=sort_order)
    db.add(folder)
    db.flush()
    return folder.id


def _make_function(db, code: str, folder_id: int, sort_order: int = 1) -> int:
    fn = Function(
        function_code=code,
        function_label=code,
        folder_id=folder_id,
        sort_order=sort_order,
    )
    db.add(fn)
    db.flush()
    return fn.function_id


def _make_role(db, name: str) -> int:
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role.id


def _make_user(
    db, email: str, name: str = "Test User", password: str = "password123"
) -> int:
    user = User(name=name, email=email, password_hash=hash_password(password))
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
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _setup_admin(engine) -> tuple[int, int, int]:
    """Create admin user with fn_expert_setting permission. Return (user_id, role_id, fn_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_function_folder(db, "資安專家", 1)
    fn_id = _make_function(db, "fn_expert_setting", folder_id, 1)
    role_id = _make_role(db, "admin")
    user_id = _make_user(db, "admin@test.com", "Admin User")
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_id


def _setup_plain_user(engine, email: str = "plain@test.com") -> tuple[int, int]:
    """Create user without fn_expert_setting permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "plain_role")
    user_id = _make_user(db, email, "Plain User")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id, role_id


def _seed_setting(engine, password_enc: str | None = None) -> int:
    """Seed singleton tb_expert_settings row (id=1) with a non-default value set."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    setting = ExpertSetting(
        id=SETTING_ID,
        is_enabled=False,
        frequency="daily",
        schedule_time="02:00",
        weekday=None,
        ssb_host="192.168.10.48",
        ssb_port=443,
        ssb_logspace="center",
        ssb_username="mpinfo",
        ssb_password_enc=password_enc,
    )
    db.add(setting)
    db.commit()
    sid = setting.id
    db.close()
    return sid


def _valid_save_payload(**overrides) -> dict:
    base = {
        "is_enabled": False,
        "frequency": "daily",
        "schedule_time": "02:00",
        "weekday": None,
        "ssb_host": "192.168.10.48",
        "ssb_port": 443,
        "ssb_logspace": "center",
        "ssb_username": "mpinfo",
        "ssb_password": "secret123",
    }
    base.update(overrides)
    return base


def _valid_ssb_test_payload(**overrides) -> dict:
    base = {
        "host": "192.168.10.48",
        "port": 443,
        "logspace": "center",
        "username": "mpinfo",
        "password": "secret123",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# GET /expert/settings
# ---------------------------------------------------------------------------


def test_get_settings_with_existing_data_returns_200(client, engine):
    """對應 T1"""
    admin_id, _, _ = _setup_admin(engine)
    from app.api.fn_expert_setting import _encrypt

    enc = _encrypt("mypassword")
    _seed_setting(engine, password_enc=enc)

    resp = client.get("/expert/settings", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    data = body["data"]
    assert "is_enabled" in data
    assert "frequency" in data
    assert "schedule_time" in data
    assert "weekday" in data
    assert "ssb_host" in data
    assert "ssb_port" in data
    assert "ssb_logspace" in data
    assert "ssb_username" in data
    assert data["ssb_password"] == "********"


def test_get_settings_no_existing_data_returns_defaults(client, engine):
    """對應 T2 — 無預先 seed 時，API 應 lazy create 並回 default 值。"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.get("/expert/settings", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["is_enabled"] is False
    assert data["frequency"] == "daily"
    # schedule_time / weekday / ssb_host etc 預設皆為 None
    assert data["schedule_time"] is None
    assert data["weekday"] is None
    assert data["ssb_host"] is None
    assert data["ssb_logspace"] is None
    assert data["ssb_username"] is None
    assert data["ssb_password"] is None


def test_get_settings_unauthenticated_returns_401(client, engine):
    """對應 T3"""
    resp = client.get("/expert/settings")
    assert resp.status_code == 401


def test_get_settings_no_permission_returns_403(client, engine):
    """對應 T15"""
    user_id, _ = _setup_plain_user(engine)

    resp = client.get("/expert/settings", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


# ---------------------------------------------------------------------------
# PUT /expert/settings
# ---------------------------------------------------------------------------


def test_save_settings_daily_returns_200(client, engine):
    """對應 T4"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.put(
        "/expert/settings",
        json=_valid_save_payload(),
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "設定已儲存"


def test_save_settings_weekly_without_weekday_returns_400(client, engine):
    """對應 T5"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.put(
        "/expert/settings",
        json=_valid_save_payload(frequency="weekly", weekday=None),
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "每週頻率需指定星期幾"


def test_save_settings_invalid_schedule_time_format_returns_400(client, engine):
    """對應 T6"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.put(
        "/expert/settings",
        json=_valid_save_payload(schedule_time="25:00"),
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "觸發時間格式錯誤"


def test_save_settings_empty_password_keeps_old_password(client, engine):
    """對應 T7"""
    admin_id, _, _ = _setup_admin(engine)
    from app.api.fn_expert_setting import _encrypt, _decrypt

    original_enc = _encrypt("original_password")
    _seed_setting(engine, password_enc=original_enc)

    resp = client.put(
        "/expert/settings",
        json=_valid_save_payload(ssb_password=""),
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 200

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    setting = db.get(ExpertSetting, SETTING_ID)
    assert setting is not None
    assert setting.ssb_password_enc is not None
    assert _decrypt(setting.ssb_password_enc) == "original_password"
    db.close()


def test_save_settings_unauthenticated_returns_401(client, engine):
    """對應 T8"""
    resp = client.put("/expert/settings", json=_valid_save_payload())
    assert resp.status_code == 401


def test_save_settings_no_permission_returns_403(client, engine):
    """對應 T16"""
    user_id, _ = _setup_plain_user(engine)

    resp = client.put(
        "/expert/settings",
        json=_valid_save_payload(),
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_save_settings_first_time_empty_password_returns_400(client, engine):
    """對應 T18 — 沒既有密碼又給空字串應擋。"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.put(
        "/expert/settings",
        json=_valid_save_payload(ssb_password=""),
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "首次儲存需提供 SSB 密碼"


def test_save_settings_empty_host_returns_400(client, engine):
    """對應 T19"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.put(
        "/expert/settings",
        json=_valid_save_payload(ssb_host=""),
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Host 為必填欄位"


def test_save_settings_is_enabled_true_persists(client, engine):
    """對應 T20"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.put(
        "/expert/settings",
        json=_valid_save_payload(is_enabled=True),
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "設定已儲存"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    setting = db.get(ExpertSetting, SETTING_ID)
    assert setting.is_enabled is True
    db.close()


def test_save_settings_is_enabled_false_persists(client, engine):
    """對應 T21"""
    admin_id, _, _ = _setup_admin(engine)
    client.put(
        "/expert/settings",
        json=_valid_save_payload(is_enabled=True),
        headers=_auth_headers(admin_id),
    )
    resp = client.put(
        "/expert/settings",
        json=_valid_save_payload(is_enabled=False),
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 200

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    setting = db.get(ExpertSetting, SETTING_ID)
    assert setting.is_enabled is False
    db.close()


def test_save_settings_empty_logspace_returns_400(client, engine):
    """對應 T13"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.put(
        "/expert/settings",
        json=_valid_save_payload(ssb_logspace=""),
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Logspace 為必填欄位"


def test_save_settings_empty_username_returns_400(client, engine):
    """對應 T14"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.put(
        "/expert/settings",
        json=_valid_save_payload(ssb_username=""),
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Username 為必填欄位"


# ---------------------------------------------------------------------------
# POST /expert/ssb-test
# ---------------------------------------------------------------------------


def _make_login_resp(token: str = "session-token-abc123"):
    """Mock 成功的 POST /api/5/login 回應."""
    mock = MagicMock()
    mock.is_success = True
    mock.status_code = 200
    mock.json.return_value = {
        "result": token,
        "error": {"code": None, "message": None},
        "warnings": [],
    }
    return mock


def _make_list_logspaces_resp(logspaces: list[str]):
    """Mock GET /api/5/search/logspace/list_logspaces 回應."""
    mock = MagicMock()
    mock.is_success = True
    mock.status_code = 200
    mock.json.return_value = {
        "result": logspaces,
        "error": {"code": None, "message": None},
        "warnings": [],
    }
    return mock


def test_ssb_test_connection_success_returns_200(client, engine):
    """對應 T9 — login 成功 + logspace 在清單內 → 200."""
    admin_id, _, _ = _setup_admin(engine)

    with patch("app.api.fn_expert_setting.httpx.Client") as mock_client_cls:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = _make_login_resp()
        mock_ctx.get.return_value = _make_list_logspaces_resp(
            ["center", "local", "ALL"]
        )
        mock_client_cls.return_value = mock_ctx

        resp = client.post(
            "/expert/ssb-test",
            json=_valid_ssb_test_payload(),
            headers=_auth_headers(admin_id),
        )

    assert resp.status_code == 200
    assert resp.json()["message"] == "連線成功"


def test_ssb_test_auth_failed_returns_502(client, engine):
    """SSB 帳密錯誤時回 502 + 認證失敗訊息."""
    admin_id, _, _ = _setup_admin(engine)

    auth_failed_resp = MagicMock()
    auth_failed_resp.is_success = True
    auth_failed_resp.status_code = 200
    auth_failed_resp.json.return_value = {
        "result": None,
        "error": {"code": "auth.failed", "message": "Invalid credentials"},
        "warnings": [],
    }

    with patch("app.api.fn_expert_setting.httpx.Client") as mock_client_cls:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = auth_failed_resp
        mock_client_cls.return_value = mock_ctx

        resp = client.post(
            "/expert/ssb-test",
            json=_valid_ssb_test_payload(),
            headers=_auth_headers(admin_id),
        )

    assert resp.status_code == 502
    assert "SSB 認證失敗" in resp.json()["detail"]


def test_ssb_test_logspace_not_found_returns_502(client, engine):
    """Logspace 不在 SSB 清單中時回 502 + 可用 logspace 提示."""
    admin_id, _, _ = _setup_admin(engine)

    with patch("app.api.fn_expert_setting.httpx.Client") as mock_client_cls:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.return_value = _make_login_resp()
        mock_ctx.get.return_value = _make_list_logspaces_resp(["local", "center"])
        mock_client_cls.return_value = mock_ctx

        resp = client.post(
            "/expert/ssb-test",
            json=_valid_ssb_test_payload(logspace="nonexistent"),
            headers=_auth_headers(admin_id),
        )

    assert resp.status_code == 502
    detail = resp.json()["detail"]
    assert "nonexistent" in detail
    assert "local" in detail and "center" in detail


def test_ssb_test_unreachable_host_returns_502(client, engine):
    """對應 T10"""
    import httpx as _httpx

    admin_id, _, _ = _setup_admin(engine)

    with patch("app.api.fn_expert_setting.httpx.Client") as mock_client_cls:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.post.side_effect = _httpx.ConnectError("Connection refused")
        mock_client_cls.return_value = mock_ctx

        resp = client.post(
            "/expert/ssb-test",
            json=_valid_ssb_test_payload(host="10.255.255.1"),
            headers=_auth_headers(admin_id),
        )

    assert resp.status_code == 502
    assert "無法連線至 SSB" in resp.json()["detail"]


def test_ssb_test_empty_host_returns_400(client, engine):
    """對應 T11"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.post(
        "/expert/ssb-test",
        json=_valid_ssb_test_payload(host=""),
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Host 為必填欄位"


def test_ssb_test_unauthenticated_returns_401(client, engine):
    """對應 T12"""
    resp = client.post("/expert/ssb-test", json=_valid_ssb_test_payload())
    assert resp.status_code == 401


def test_ssb_test_no_permission_returns_403(client, engine):
    """對應 T17"""
    user_id, _ = _setup_plain_user(engine)

    resp = client.post(
        "/expert/ssb-test",
        json=_valid_ssb_test_payload(),
        headers=_auth_headers(user_id),
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"
