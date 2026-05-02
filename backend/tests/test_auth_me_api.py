"""
Tests for GET /api/users/me API.

Covers test spec IDs T6 and T7 from _fn_auth_test_api.md.
"""

from sqlalchemy.orm import sessionmaker

from app.db.models.fn_user_role import Role, User, UserRole
from app.db.models.fn_auth_sidebar import Function, FunctionFolder, RoleFunction
from app.utils.util_store import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_tables(engine) -> None:
    """Create sidebar-related tables in the test DB."""
    FunctionFolder.__table__.create(bind=engine, checkfirst=True)
    Function.__table__.create(bind=engine, checkfirst=True)
    RoleFunction.__table__.create(bind=engine, checkfirst=True)


def _seed_folders_and_functions(engine) -> None:
    """Seed tb_function_folder, tb_functions."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    # Create folders
    db.add(FunctionFolder(id=1, name="AI 夥伴", default_open=True, sort_order=1))
    db.add(FunctionFolder(id=2, name="設定", default_open=False, sort_order=2))
    db.flush()
    # Create functions (fn_setting removed per issue-171)
    for func_id, func_name, folder_id, sort in [
        (1, "fn_partner", 1, 1),
        (2, "fn_km", 1, 2),
        (3, "fn_ai_config", 1, 3),
        (4, "fn_user", 2, 1),
        (5, "fn_role", 2, 2),
    ]:
        db.add(Function(function_id=func_id, function_name=func_name, folder_id=folder_id, sort_order=sort))
    db.commit()
    db.close()


def _make_role(db, name: str) -> int:
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role.id


def _make_user(db, email: str, name: str = "Test User") -> int:
    user = User(name=name, email=email, password_hash=hash_password("password123"))
    db.add(user)
    db.flush()
    return user.id


def _assign_role(db, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _bind_functions(db, role_id: int, function_ids: list[int]) -> None:
    for fid in function_ids:
        db.add(RoleFunction(role_id=role_id, function_id=fid))
    db.flush()


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_me_returns_200_with_functions(client, engine):
    """對應 T6：已登入，使用者具備若干功能權限，GET /api/users/me 回傳 200 及 functions 陣列（不含 fn_setting）。"""
    _setup_tables(engine)
    _seed_folders_and_functions(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "admin_role")
    user_id = _make_user(db, "rex@test.com", name="Rex Shen")
    _assign_role(db, user_id, role_id)
    _bind_functions(db, role_id, [1, 2, 3, 4, 5])
    db.commit()
    db.close()

    resp = client.get("/api/users/me", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    data = body["data"]
    assert data["id"] == user_id
    assert data["name"] == "Rex Shen"
    assert data["email"] == "rex@test.com"
    assert isinstance(data["functions"], list)
    assert len(data["functions"]) == 5
    assert set(data["functions"]) == {
        "fn_partner", "fn_km", "fn_ai_config", "fn_user", "fn_role"
    }
    assert "fn_setting" not in data["functions"]


def test_get_me_returns_partial_functions(client, engine):
    """對應 T6（部分權限）：使用者僅具備 fn_partner、fn_km，functions 只含有權限的功能。"""
    _setup_tables(engine)
    _seed_folders_and_functions(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "partial_role")
    user_id = _make_user(db, "robert@test.com", name="Robert")
    _assign_role(db, user_id, role_id)
    _bind_functions(db, role_id, [1, 2])  # fn_partner, fn_km only
    db.commit()
    db.close()

    resp = client.get("/api/users/me", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert set(data["functions"]) == {"fn_partner", "fn_km"}


def test_get_me_unauthenticated_returns_401(client, engine):
    """對應 T7：未登入或 token 已過期，GET /api/users/me 應回 401。"""
    resp = client.get("/api/users/me")
    assert resp.status_code == 401


def test_get_me_expired_token_returns_401(client, engine):
    """對應 T7（過期 token）：帶過期或無效 token，應回 401。"""
    resp = client.get(
        "/api/users/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401
