"""
Tests for fn_role APIs:
  GET    /api/roles
  POST   /api/roles
  PATCH  /api/roles/{name}
  DELETE /api/roles/{name}
  GET    /api/functions/options
"""

from sqlalchemy.orm import Session, sessionmaker

from app.core.security import create_access_token, hash_password
from app.db.models.user import Function, Role, RoleFunction, User, UserRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_function(db: Session, function_id: int, function_name: str) -> int:
    fn = Function(function_id=function_id, function_name=function_name)
    db.add(fn)
    db.flush()
    return fn.function_id


def _make_role(db: Session, name: str) -> int:
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role.id


def _make_user(
    db: Session, email: str, name: str = "Test User", password: str = "password123"
) -> int:
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _assign_function(db: Session, role_id: int, function_id: int) -> None:
    db.add(RoleFunction(role_id=role_id, function_id=function_id))
    db.flush()


def _auth_headers(user_id: int) -> dict:
    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


def _setup_admin(engine) -> tuple[int, int, int]:
    """Create fn_role-permitted role + user. Return (user_id, role_id, fn_role_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    fn_user_id = _make_function(db, 1, "fn_user")
    fn_role_id = _make_function(db, 2, "fn_role")
    role_id = _make_role(db, "admin")
    _assign_function(db, role_id, fn_user_id)
    _assign_function(db, role_id, fn_role_id)
    user_id = _make_user(db, "admin@test.com", name="Admin")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_role_id


def _setup_no_perm_user(engine) -> int:
    """Create a user without fn_role permission. Return user_id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "noperm_role")
    user_id = _make_user(db, "noperm@test.com", name="NoPerm")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id


# ---------------------------------------------------------------------------
# GET /api/roles
# ---------------------------------------------------------------------------


def test_list_roles_returns_200_with_functions(client, engine):
    """對應 T1"""
    admin_id, admin_role_id, fn_role_id = _setup_admin(engine)

    resp = client.get("/api/roles", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    data = body["data"]
    assert isinstance(data, list)
    # admin role should appear with functions array
    admin_entry = next((r for r in data if r["name"] == "admin"), None)
    assert admin_entry is not None
    assert "functions" in admin_entry
    assert isinstance(admin_entry["functions"], list)
    assert "users" in admin_entry


def test_list_roles_no_permission_returns_403(client, engine):
    """對應 T2"""
    user_id = _setup_no_perm_user(engine)

    resp = client.get("/api/roles", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_list_roles_filter_by_keyword(client, engine):
    """對應 T3"""
    admin_id, _, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_role(db, "管理員角色")
    _make_role(db, "一般角色")
    db.commit()
    db.close()

    resp = client.get("/api/roles?keyword=管理員", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    names = [r["name"] for r in data]
    assert "管理員角色" in names
    assert "一般角色" not in names


def test_list_roles_unauthenticated_returns_401(client, engine):
    """未登入應回 401"""
    resp = client.get("/api/roles")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/roles
# ---------------------------------------------------------------------------


def test_create_role_returns_201(client, engine):
    """對應 T4"""
    admin_id, _, fn_role_id = _setup_admin(engine)

    payload = {"name": "測試角色", "function_ids": [fn_role_id]}
    resp = client.post("/api/roles", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"


def test_create_role_duplicate_name_returns_400(client, engine):
    """對應 T5"""
    admin_id, _, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_role(db, "測試角色")
    db.commit()
    db.close()

    payload = {"name": "測試角色"}
    resp = client.post("/api/roles", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "此角色名稱已存在"


def test_create_role_empty_name_returns_400(client, engine):
    """對應 T6"""
    admin_id, _, _ = _setup_admin(engine)

    payload = {"name": ""}
    resp = client.post("/api/roles", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "角色名稱未填寫"


def test_create_role_no_permission_returns_403(client, engine):
    """無 fn_role 權限新增角色應回 403"""
    user_id = _setup_no_perm_user(engine)

    payload = {"name": "新角色"}
    resp = client.post("/api/roles", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /api/roles/{name}
# ---------------------------------------------------------------------------


def test_update_role_returns_200(client, engine):
    """對應 T7"""
    admin_id, _, fn_role_id = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_role(db, "測試角色")
    db.commit()
    db.close()

    payload = {"name": "修改後角色", "function_ids": [fn_role_id]}
    resp = client.patch(
        "/api/roles/測試角色", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"


def test_update_role_not_found_returns_404(client, engine):
    """對應 T8"""
    admin_id, _, _ = _setup_admin(engine)

    payload = {"name": "任意名稱"}
    resp = client.patch(
        "/api/roles/不存在的角色", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "角色不存在"


def test_update_role_name_conflict_returns_400(client, engine):
    """對應 T9"""
    admin_id, _, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_role(db, "角色A")
    _make_role(db, "角色B")
    db.commit()
    db.close()

    payload = {"name": "角色B"}
    resp = client.patch(
        "/api/roles/角色A", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "此角色名稱已被其他角色使用"


def test_update_role_unauthenticated_returns_401(client, engine):
    """未登入應回 401"""
    resp = client.patch("/api/roles/任意角色", json={"name": "x"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/roles/{name}
# ---------------------------------------------------------------------------


def test_delete_role_returns_200(client, engine):
    """對應 T10 — 刪除後 tb_roles、tb_role_function、tb_user_roles 對應紀錄均移除"""
    admin_id, _, fn_role_id = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    target_role_id = _make_role(db, "待刪角色")
    # assign a function and a user to this role to verify cascade delete
    _assign_function(db, target_role_id, fn_role_id)
    target_user_id = _make_user(db, "target_del@test.com")
    _assign_role(db, target_user_id, target_role_id)
    db.commit()
    db.close()

    resp = client.delete("/api/roles/待刪角色", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    # Verify the role is gone from list
    resp2 = client.get("/api/roles", headers=_auth_headers(admin_id))
    names = [r["name"] for r in resp2.json()["data"]]
    assert "待刪角色" not in names


def test_delete_role_not_found_returns_404(client, engine):
    """對應 T11"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.delete("/api/roles/不存在的角色", headers=_auth_headers(admin_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "角色不存在"


def test_delete_role_unauthenticated_returns_401(client, engine):
    """未登入應回 401"""
    resp = client.delete("/api/roles/任意角色")
    assert resp.status_code == 401


def test_delete_role_no_permission_returns_403(client, engine):
    """無 fn_role 權限刪除角色應回 403"""
    user_id = _setup_no_perm_user(engine)

    resp = client.delete("/api/roles/任意角色", headers=_auth_headers(user_id))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/functions/options
# ---------------------------------------------------------------------------


def test_get_function_options_returns_200(client, engine):
    """對應 T18"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.get("/api/functions/options", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    data = body["data"]
    assert isinstance(data, list)
    fn_names = [f["function_name"] for f in data]
    assert "fn_user" in fn_names
    assert "fn_role" in fn_names


def test_get_function_options_unauthenticated_returns_401(client, engine):
    """對應 T19"""
    resp = client.get("/api/functions/options")
    assert resp.status_code == 401
