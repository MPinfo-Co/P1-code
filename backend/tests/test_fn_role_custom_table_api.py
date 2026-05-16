"""
Tests for fn_role custom_table_ids extensions:
  POST  /roles — T26, T26b, T26c
  PATCH /roles/{name} — T27, T27b, T27c
  GET   /roles — T28, T28b, T28c
"""

from sqlalchemy.orm import Session, sessionmaker

from app.db.models.fn_custom_table import CustomTable, RoleCustomTable
from app.db.models.function_access import (
    FunctionFolder,
    FunctionItems as Function,
    RoleFunction,
)
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_folder(db: Session, name: str = "設定") -> int:
    folder = FunctionFolder(folder_code=name, folder_label=name, sort_order=2)
    db.add(folder)
    db.flush()
    return folder.id


def _make_function(db: Session, code: str, folder_id: int) -> int:
    fn = Function(
        function_code=code,
        function_label=code,
        folder_id=folder_id,
        sort_order=1,
    )
    db.add(fn)
    db.flush()
    return fn.function_id


def _make_role(db: Session, name: str) -> int:
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role.id


def _make_user(db: Session, email: str, name: str = "Test") -> int:
    user = User(name=name, email=email, password_hash=hash_password("password"))
    db.add(user)
    db.flush()
    return user.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _grant_function(db: Session, role_id: int, fn_id: int) -> None:
    db.add(RoleFunction(role_id=role_id, function_id=fn_id))
    db.flush()


def _make_custom_table(db: Session, name: str) -> int:
    t = CustomTable(name=name)
    db.add(t)
    db.flush()
    return t.id


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _setup_admin_with_fn_role(engine, email: str = "admin_ct@test.com"):
    """Create admin user with fn_role permission.

    NOTE: each test uses a separate in-memory engine, so "fn_role" function code
    uniqueness constraint is not violated across tests.
    """
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_folder(db, "設定")
    # Function code must be exactly "fn_role" to match roles.py permission check
    fn_role_id = _make_function(db, "fn_role", folder_id)
    role_id = _make_role(db, f"admin_{email}")
    user_id = _make_user(db, email, name="Admin")
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_role_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_role_id


def _setup_plain_user(engine, email: str = "plain_ct@test.com"):
    """Create a user without fn_role permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, f"plain_{email}")
    user_id = _make_user(db, email, name="Plain")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id, role_id


# ---------------------------------------------------------------------------
# POST /roles — custom_table_ids: T26, T26b, T26c
# ---------------------------------------------------------------------------


def test_add_role_with_custom_table_ids_returns_201(client, engine):
    """對應 T26"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine, "ct_add@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t1 = _make_custom_table(db, "CT_T26_Table1")
    t2 = _make_custom_table(db, "CT_T26_Table2")
    db.commit()
    db.close()

    payload = {"name": "CT_T26_Role", "custom_table_ids": [t1, t2]}
    resp = client.post("/roles", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"

    # Verify tb_role_custom_tables was populated
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    created_role = db.query(Role).filter(Role.name == "CT_T26_Role").first()
    assert created_role is not None
    ct_rows = (
        db.query(RoleCustomTable)
        .filter(RoleCustomTable.role_id == created_role.id)
        .all()
    )
    assert len(ct_rows) == 2
    db.close()


def test_add_role_nonexistent_custom_table_ids_returns_404(client, engine):
    """對應 T26b"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine, "ct_add404@test.com")

    payload = {"name": "CT_T26b_Role", "custom_table_ids": [9999]}
    resp = client.post("/roles", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "指定的資料表不存在"


def test_add_role_no_fn_role_permission_returns_403(client, engine):
    """對應 T26c"""
    plain_id, _ = _setup_plain_user(engine, "ct_plain403@test.com")

    payload = {"name": "CT_T26c_Role", "custom_table_ids": [1]}
    resp = client.post("/roles", json=payload, headers=_auth_headers(plain_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


# ---------------------------------------------------------------------------
# PATCH /roles/{name} — custom_table_ids: T27, T27b, T27c
# ---------------------------------------------------------------------------


def test_update_role_with_custom_table_ids_returns_200(client, engine):
    """對應 T27"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine, "ct_upd@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_role(db, "CT_T27_Role")
    t3 = _make_custom_table(db, "CT_T27_Table3")
    db.commit()
    db.close()

    payload = {"custom_table_ids": [t3]}
    resp = client.patch(
        "/roles/CT_T27_Role",
        json=payload,
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    # Verify tb_role_custom_tables updated
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role = db.query(Role).filter(Role.name == "CT_T27_Role").first()
    ct_rows = db.query(RoleCustomTable).filter(RoleCustomTable.role_id == role.id).all()
    assert len(ct_rows) == 1
    assert ct_rows[0].table_id == t3
    db.close()


def test_update_role_nonexistent_custom_table_ids_returns_404(client, engine):
    """對應 T27b"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine, "ct_upd404@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_role(db, "CT_T27b_Role")
    db.commit()
    db.close()

    payload = {"custom_table_ids": [9999]}
    resp = client.patch(
        "/roles/CT_T27b_Role",
        json=payload,
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "指定的資料表不存在"


def test_update_role_not_found_returns_404(client, engine):
    """對應 T27c"""
    admin_id, _, _ = _setup_admin_with_fn_role(engine, "ct_upd_nf@test.com")

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t_id = _make_custom_table(db, "CT_T27c_Table")
    db.commit()
    db.close()

    payload = {"custom_table_ids": [t_id]}
    resp = client.patch(
        "/roles/不存在的角色_CT",
        json=payload,
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "角色不存在"


# ---------------------------------------------------------------------------
# GET /roles — custom_table_ids: T28, T28b, T28c
# ---------------------------------------------------------------------------


def test_list_roles_includes_custom_table_ids(client, engine):
    """對應 T28"""
    admin_id, admin_role_id, _ = _setup_admin_with_fn_role(engine, "ct_list@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    t1 = _make_custom_table(db, "CT_T28_Table1")
    t2 = _make_custom_table(db, "CT_T28_Table2")
    db.add(RoleCustomTable(role_id=admin_role_id, table_id=t1))
    db.add(RoleCustomTable(role_id=admin_role_id, table_id=t2))
    db.commit()
    db.close()

    resp = client.get("/roles", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    items = resp.json()["items"]
    admin_item = next((r for r in items if r["name"] == "admin_ct_list@test.com"), None)
    assert admin_item is not None
    assert "custom_table_ids" in admin_item
    ct_ids = set(admin_item["custom_table_ids"])
    assert t1 in ct_ids and t2 in ct_ids


def test_list_roles_unauthenticated_returns_401(client, engine):
    """對應 T28b"""
    resp = client.get("/roles")
    assert resp.status_code == 401


def test_list_roles_no_fn_role_permission_returns_403(client, engine):
    """對應 T28c"""
    plain_id, _ = _setup_plain_user(engine, "ct_403_list@test.com")

    resp = client.get("/roles", headers=_auth_headers(plain_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"
