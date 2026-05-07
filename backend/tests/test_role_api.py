"""
Tests for fn_role APIs:
  GET    /api/roles
  POST   /api/roles
  PATCH  /api/roles/{name}
  DELETE /api/roles/{name}
  GET    /api/roles/options
  GET    /api/functions/options
"""

from sqlalchemy.orm import Session, sessionmaker

from app.utils.util_store import create_access_token, hash_password
from app.db.models.function_access import FunctionItems as Function, FunctionFolder, RoleFunction
from app.db.models.user_role import Role, User, UserRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_function_folder(db: Session, name: str = "設定", sort_order: int = 2) -> int:
    folder = FunctionFolder(folder_code=name, folder_label=name, default_open=False, sort_order=sort_order)
    db.add(folder)
    db.flush()
    return folder.id


def _make_function(db: Session, name: str, folder_id: int, sort_order: int = 1) -> int:
    fn = Function(function_code=name, function_label=name, folder_id=folder_id, sort_order=sort_order)
    db.add(fn)
    db.flush()
    return fn.function_id


def _make_role(db: Session, name: str) -> int:
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role.id


def _make_user(db: Session, email: str, name: str = "Test User", password: str = "password123") -> int:
    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    return user.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _grant_function(db: Session, role_id: int, function_id: int) -> None:
    db.add(RoleFunction(role_id=role_id, function_id=function_id))
    db.flush()


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _setup_admin_with_fn_role(engine):
    """Create admin user with fn_role permission. Return (user_id, role_id, fn_role_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_function_folder(db, "設定", 2)
    fn_role_id = _make_function(db, "fn_role", folder_id, 2)
    role_id = _make_role(db, "admin")
    user_id = _make_user(db, "admin@test.com", name="Admin User")
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_role_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_role_id


def _setup_plain_user(engine, email: str = "plain@test.com"):
    """Create a user without fn_role permission. Return (user_id, role_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "plain_role")
    user_id = _make_user(db, email, name="Plain User")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id, role_id


# ---------------------------------------------------------------------------
# GET /api/roles — T1, T2, T3
# ---------------------------------------------------------------------------


def test_list_roles_returns_200(client, engine):
    """對應 T1"""
    admin_id, admin_role_id, _ = _setup_admin_with_fn_role(engine)

    resp = client.get("/api/roles", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert isinstance(body["data"], list)
    names = [r["name"] for r in body["data"]]
    assert "admin" in names


def test_list_roles_no_permission_returns_403(client, engine):
    """對應 T2"""
    user_id, _ = _setup_plain_user(engine)

    resp = client.get("/api/roles", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_list_roles_keyword_filter(client, engine):
    """對應 T3"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_role(db, "管理員")
    _make_role(db, "普通角色")
    db.commit()
    db.close()

    resp = client.get("/api/roles?keyword=管理員", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    names = [r["name"] for r in data]
    assert "管理員" in names
    assert "普通角色" not in names


def test_list_roles_unauthenticated_returns_401(client, engine):
    """未登入 GET /api/roles 應回 401"""
    resp = client.get("/api/roles")
    assert resp.status_code == 401


def test_list_roles_includes_users_and_functions(client, engine):
    """對應 T1：每筆角色含使用者陣列及 functions 陣列"""
    admin_id, admin_role_id, fn_role_id = _setup_admin_with_fn_role(engine)

    resp = client.get("/api/roles", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    admin_item = next((r for r in data if r["name"] == "admin"), None)
    assert admin_item is not None
    assert "users" in admin_item
    assert "functions" in admin_item
    assert isinstance(admin_item["users"], list)
    assert isinstance(admin_item["functions"], list)


# ---------------------------------------------------------------------------
# POST /api/roles — T4, T5, T6
# ---------------------------------------------------------------------------


def test_add_role_returns_201(client, engine):
    """對應 T4"""
    admin_id, _, fn_role_id = _setup_admin_with_fn_role(engine)

    payload = {"name": "測試角色", "function_ids": [fn_role_id]}
    resp = client.post("/api/roles", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"


def test_add_role_duplicate_name_returns_400(client, engine):
    """對應 T5"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_role(db, "測試角色")
    db.commit()
    db.close()

    payload = {"name": "測試角色"}
    resp = client.post("/api/roles", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "此角色名稱已存在"


def test_add_role_empty_name_returns_400(client, engine):
    """對應 T6"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine)

    payload = {"name": ""}
    resp = client.post("/api/roles", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "角色名稱未填寫"


def test_add_role_no_permission_returns_403(client, engine):
    """無權限 POST /api/roles 應回 403"""
    user_id, _ = _setup_plain_user(engine)

    payload = {"name": "SomeRole"}
    resp = client.post("/api/roles", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 403


def test_add_role_unauthenticated_returns_401(client, engine):
    """未登入 POST /api/roles 應回 401"""
    resp = client.post("/api/roles", json={"name": "SomeRole"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /api/roles/{name} — T7, T8, T9
# ---------------------------------------------------------------------------


def test_update_role_returns_200(client, engine):
    """對應 T7"""
    admin_id, _, fn_role_id = _setup_admin_with_fn_role(engine)

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
    admin_id, _, _ = _setup_admin_with_fn_role(engine)

    resp = client.patch(
        "/api/roles/不存在的角色",
        json={"name": "anyname"},
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "角色不存在"


def test_update_role_duplicate_name_returns_400(client, engine):
    """對應 T9"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_role(db, "角色A")
    _make_role(db, "角色B")
    db.commit()
    db.close()

    resp = client.patch(
        "/api/roles/角色A",
        json={"name": "角色B"},
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "此角色名稱已被其他角色使用"


def test_update_role_no_permission_returns_403(client, engine):
    """無權限 PATCH /api/roles/{name} 應回 403"""
    plain_id, _ = _setup_plain_user(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_role(db, "somrole")
    db.commit()
    db.close()

    resp = client.patch(
        "/api/roles/somrole",
        json={"name": "newname"},
        headers=_auth_headers(plain_id),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/roles/{name} — T10, T11
# ---------------------------------------------------------------------------


def test_delete_role_returns_200(client, engine):
    """對應 T10"""
    admin_id, _, fn_role_id = _setup_admin_with_fn_role(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "待刪角色")
    user_id2 = _make_user(db, "member@test.com", name="Member")
    _assign_role(db, user_id2, role_id)
    _grant_function(db, role_id, fn_role_id)
    db.commit()
    db.close()

    resp = client.delete("/api/roles/待刪角色", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    # Verify role is gone
    resp2 = client.get("/api/roles", headers=_auth_headers(admin_id))
    names = [r["name"] for r in resp2.json()["data"]]
    assert "待刪角色" not in names


def test_delete_role_not_found_returns_404(client, engine):
    """對應 T11"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine)

    resp = client.delete("/api/roles/不存在的角色", headers=_auth_headers(admin_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "角色不存在"


def test_delete_role_no_permission_returns_403(client, engine):
    """無權限 DELETE /api/roles/{name} 應回 403"""
    plain_id, _ = _setup_plain_user(engine)

    resp = client.delete("/api/roles/plain_role", headers=_auth_headers(plain_id))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/roles/options — T12, T13
# ---------------------------------------------------------------------------


def test_get_role_options_returns_200(client, engine):
    """對應 T12"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine)

    resp = client.get("/api/roles/options", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert isinstance(body["data"], list)
    assert all("id" in item and "name" in item for item in body["data"])


def test_get_role_options_unauthenticated_returns_401(client, engine):
    """對應 T13"""
    resp = client.get("/api/roles/options")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/functions/options — T14, T15
# ---------------------------------------------------------------------------


def test_get_function_options_returns_200(client, engine):
    """對應 T14"""
    admin_id, _, fn_role_id = _setup_admin_with_fn_role(engine)

    resp = client.get("/api/functions/options", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1
    first = body["data"][0]
    assert "function_id" in first
    assert "function_code" in first


def test_get_function_options_sorted_by_id(client, engine):
    """對應 T14：依 function_id 升冪排序"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id2 = _make_function_folder(db, "AI 夥伴", 1)
    _make_function(db, "fn_partner", folder_id2, 1)
    _make_function(db, "fn_ai_config", folder_id2, 2)
    db.commit()
    db.close()

    resp = client.get("/api/functions/options", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    ids = [item["function_id"] for item in data]
    assert ids == sorted(ids)


def test_get_function_options_unauthenticated_returns_401(client, engine):
    """對應 T15"""
    resp = client.get("/api/functions/options")
    assert resp.status_code == 401
