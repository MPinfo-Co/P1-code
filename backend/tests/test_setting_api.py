"""Tests for fn_setting APIs:
GET /api/settings
PATCH /api/settings/{param_code}
GET /api/settings/options/param-types
"""

from sqlalchemy.orm import Session

from app.db.models.fn_setting import SystemParam
from app.db.models.fn_user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(db: Session, email: str, name: str = "Test User") -> int:
    user = User(name=name, email=email, password_hash=hash_password("pw"), is_active=True)
    db.add(user)
    db.flush()
    return user.id


def _make_role(db: Session, name: str, can_manage_settings: bool = False) -> int:
    role = Role(name=name, can_manage_settings=can_manage_settings)
    db.add(role)
    db.flush()
    return role.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _make_param(
    db: Session, param_type: str, param_code: str, param_value: str
) -> None:
    db.add(
        SystemParam(param_type=param_type, param_code=param_code, param_value=param_value)
    )
    db.flush()


# ---------------------------------------------------------------------------
# GET /api/settings
# ---------------------------------------------------------------------------


def test_list_settings_returns_all_params(client, engine):
    """對應 T1"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "admin@t1.com")
        rid = _make_role(db, "管理員T1", can_manage_settings=True)
        _assign_role(db, uid, rid)
        _make_param(db, "SSB連線", "SSB_API_URL", "https://example.com")
        _make_param(db, "系統", "SESSION_TIMEOUT_MIN", "30")
        db.commit()

    resp = client.get("/api/settings", headers=_token(uid))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    codes = [item["param_code"] for item in body["data"]]
    assert "SSB_API_URL" in codes
    assert "SESSION_TIMEOUT_MIN" in codes
    # 每筆包含必要欄位
    for item in body["data"]:
        assert "param_type" in item
        assert "param_code" in item
        assert "param_value" in item


def test_list_settings_no_permission_returns_403(client, engine):
    """對應 T2"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "user@t2.com")
        rid = _make_role(db, "一般角色T2", can_manage_settings=False)
        _assign_role(db, uid, rid)
        db.commit()

    resp = client.get("/api/settings", headers=_token(uid))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_list_settings_unauthenticated_returns_401(client):
    """對應 T3"""
    resp = client.get("/api/settings")
    assert resp.status_code == 401


def test_list_settings_filter_by_param_type(client, engine):
    """對應 T4"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "admin@t4.com")
        rid = _make_role(db, "管理員T4", can_manage_settings=True)
        _assign_role(db, uid, rid)
        _make_param(db, "SSB連線", "SSB_API_URL", "https://ssb.example.com")
        _make_param(db, "系統", "SESSION_TIMEOUT_MIN", "60")
        db.commit()

    resp = client.get("/api/settings?param_type=SSB連線", headers=_token(uid))
    assert resp.status_code == 200
    body = resp.json()
    assert all(item["param_type"] == "SSB連線" for item in body["data"])
    assert len(body["data"]) == 1
    assert body["data"][0]["param_code"] == "SSB_API_URL"


# ---------------------------------------------------------------------------
# PATCH /api/settings/{param_code}
# ---------------------------------------------------------------------------


def test_update_setting_success(client, engine):
    """對應 T5"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "admin@t5.com")
        rid = _make_role(db, "管理員T5", can_manage_settings=True)
        _assign_role(db, uid, rid)
        _make_param(db, "系統", "SESSION_TIMEOUT_MIN", "60")
        db.commit()

    resp = client.patch(
        "/api/settings/SESSION_TIMEOUT_MIN",
        json={"param_value": "30"},
        headers=_token(uid),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"


def test_update_setting_no_permission_returns_403(client, engine):
    """對應 T6"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "user@t6.com")
        rid = _make_role(db, "一般角色T6", can_manage_settings=False)
        _assign_role(db, uid, rid)
        db.commit()

    resp = client.patch(
        "/api/settings/SESSION_TIMEOUT_MIN",
        json={"param_value": "30"},
        headers=_token(uid),
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_update_setting_not_found_returns_404(client, engine):
    """對應 T7"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "admin@t7.com")
        rid = _make_role(db, "管理員T7", can_manage_settings=True)
        _assign_role(db, uid, rid)
        db.commit()

    resp = client.patch(
        "/api/settings/NOT_EXIST_CODE",
        json={"param_value": "abc"},
        headers=_token(uid),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "參數不存在"


def test_update_setting_empty_value_returns_400(client, engine):
    """對應 T8"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "admin@t8.com")
        rid = _make_role(db, "管理員T8", can_manage_settings=True)
        _assign_role(db, uid, rid)
        _make_param(db, "系統", "SESSION_TIMEOUT_MIN", "60")
        db.commit()

    resp = client.patch(
        "/api/settings/SESSION_TIMEOUT_MIN",
        json={"param_value": ""},
        headers=_token(uid),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "參數值不可為空"


def test_update_setting_unauthenticated_returns_401(client):
    """對應 T3 (update variant)"""
    resp = client.patch(
        "/api/settings/SESSION_TIMEOUT_MIN",
        json={"param_value": "30"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/settings/options/param-types
# ---------------------------------------------------------------------------


def test_list_param_type_options_returns_distinct_sorted(client, engine):
    """對應 T9"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "admin@t9.com")
        rid = _make_role(db, "管理員T9", can_manage_settings=True)
        _assign_role(db, uid, rid)
        _make_param(db, "SSB連線", "SSB_API_URL", "https://ssb.example.com")
        _make_param(db, "系統", "SESSION_TIMEOUT_MIN", "60")
        _make_param(db, "系統", "MAX_LOGIN_ATTEMPTS", "5")
        db.commit()

    resp = client.get("/api/settings/options/param-types", headers=_token(uid))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    data = body["data"]
    assert isinstance(data, list)
    # 不重複
    assert len(data) == len(set(data))
    # 包含預期類型
    assert "SSB連線" in data
    assert "系統" in data
    # 升冪排序
    assert data == sorted(data)


def test_list_param_type_options_unauthenticated_returns_401(client):
    """對應 T10"""
    resp = client.get("/api/settings/options/param-types")
    assert resp.status_code == 401
