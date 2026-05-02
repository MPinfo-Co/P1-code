"""
Tests for GET /api/users/me API.
對應 _fn_auth_test_api.md T6, T7
"""

from sqlalchemy.orm import Session, sessionmaker

from app.utils.util_store import create_access_token, hash_password
from app.db.models.fn_user_role import Role, User, UserRole
from app.db.models.fn_sidebar import Function, FunctionFolder, RoleFunction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_sidebar_data(db: Session) -> tuple[int, int]:
    """Seed tb_function_folder and tb_functions; return (folder_ai_id, folder_setting_id)."""
    folder_ai = FunctionFolder(id=1, name="AI 夥伴", default_open=True, sort_order=1)
    folder_setting = FunctionFolder(id=2, name="設定", default_open=False, sort_order=2)
    db.add_all([folder_ai, folder_setting])
    db.flush()

    functions = [
        Function(function_id=1, function_name="fn_partner", folder_id=1, sort_order=1),
        Function(function_id=2, function_name="fn_km", folder_id=1, sort_order=2),
        Function(function_id=3, function_name="fn_ai_config", folder_id=1, sort_order=3),
        Function(function_id=4, function_name="fn_user", folder_id=2, sort_order=1),
        Function(function_id=5, function_name="fn_role", folder_id=2, sort_order=2),
        Function(function_id=6, function_name="fn_setting", folder_id=2, sort_order=3),
    ]
    db.add_all(functions)
    db.flush()
    return folder_ai.id, folder_setting.id


def _make_role(db: Session, name: str) -> int:
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role.id


def _make_user(db: Session, email: str, name: str = "Test User") -> int:
    user = User(
        name=name,
        email=email,
        password_hash=hash_password("password123"),
    )
    db.add(user)
    db.flush()
    return user.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _bind_role_functions(db: Session, role_id: int, function_ids: list[int]) -> None:
    for fid in function_ids:
        db.add(RoleFunction(role_id=role_id, function_id=fid))
    db.flush()


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# T6: GET /api/users/me — 已登入，返回使用者資料與 functions 陣列
# ---------------------------------------------------------------------------


def test_get_me_returns_200_with_functions(client, engine):
    """對應 T6：已登入（有效 JWT），使用者具備若干功能權限，GET /api/users/me 回傳 200 含 functions"""
    Session_ = sessionmaker(bind=engine)
    db = Session_()

    _seed_sidebar_data(db)
    role_id = _make_role(db, "admin_role")
    user_id = _make_user(db, "admin@test.com", name="Rex Shen")
    _assign_role(db, user_id, role_id)
    _bind_role_functions(db, role_id, [1, 2, 3, 4, 5, 6])
    db.commit()
    db.close()

    resp = client.get("/api/users/me", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "成功"
    data = body["data"]
    assert data["id"] == user_id
    assert data["name"] == "Rex Shen"
    assert data["email"] == "admin@test.com"
    assert isinstance(data["functions"], list)
    assert set(data["functions"]) == {
        "fn_partner", "fn_km", "fn_ai_config", "fn_user", "fn_role", "fn_setting"
    }


def test_get_me_returns_only_permitted_functions(client, engine):
    """已登入，使用者只有部分功能權限，functions 陣列只包含有權限的功能"""
    Session_ = sessionmaker(bind=engine)
    db = Session_()

    _seed_sidebar_data(db)
    role_id = _make_role(db, "user_role")
    user_id = _make_user(db, "user@test.com", name="Plain User")
    _assign_role(db, user_id, role_id)
    # 僅綁定 fn_partner, fn_km
    _bind_role_functions(db, role_id, [1, 2])
    db.commit()
    db.close()

    resp = client.get("/api/users/me", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert set(data["functions"]) == {"fn_partner", "fn_km"}
    assert "fn_role" not in data["functions"]
    assert "fn_setting" not in data["functions"]


def test_get_me_returns_empty_functions_when_no_role(client, engine):
    """已登入，使用者沒有綁定任何角色功能，functions 為空陣列"""
    Session_ = sessionmaker(bind=engine)
    db = Session_()

    _seed_sidebar_data(db)
    role_id = _make_role(db, "no_func_role")
    user_id = _make_user(db, "norole@test.com", name="No Role User")
    _assign_role(db, user_id, role_id)
    # 不綁定任何功能
    db.commit()
    db.close()

    resp = client.get("/api/users/me", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["functions"] == []


# ---------------------------------------------------------------------------
# T7: GET /api/users/me — 未登入或 token 過期，回傳 401
# ---------------------------------------------------------------------------


def test_get_me_unauthenticated_returns_401(client, engine):
    """對應 T7：未帶 token，GET /api/users/me 應回 401"""
    resp = client.get("/api/users/me")
    assert resp.status_code == 401


def test_get_me_invalid_token_returns_401(client, engine):
    """對應 T7：帶無效 token，GET /api/users/me 應回 401"""
    resp = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401
