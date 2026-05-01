"""Tests for fn_dept APIs:
  GET    /api/dept
  POST   /api/dept
  PATCH  /api/dept/{id}
  PATCH  /api/dept/{id}/toggle
  GET    /api/dept/{id}/members
  GET    /api/dept/options
"""

from sqlalchemy.orm import Session, sessionmaker

from app.db.models.fn_dept import Department
from app.db.models.fn_user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_role(db: Session, name: str, can_manage_depts: bool = False) -> int:
    role = Role(name=name, can_manage_depts=can_manage_depts)
    db.add(role)
    db.flush()
    return role.id


def _make_user(db: Session, email: str, name: str = "Test User", dept_id: int | None = None) -> int:
    user = User(
        name=name,
        email=email,
        password_hash=hash_password("password123"),
        is_active=True,
        department_id=dept_id,
    )
    db.add(user)
    db.flush()
    return user.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _make_dept(
    db: Session,
    name: str,
    code: str,
    parent_id: int | None = None,
    is_active: bool = True,
) -> int:
    dept = Department(name=name, code=code, parent_id=parent_id, is_active=is_active)
    db.add(dept)
    db.flush()
    return dept.id


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _setup_admin(engine):
    """Create user with fn_dept permission. Returns (user_id, role_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "dept_admin", can_manage_depts=True)
    user_id = _make_user(db, "admin@dept.com", name="Dept Admin")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id, role_id


def _setup_plain_user(engine, email: str = "plain@dept.com"):
    """Create user without fn_dept permission. Returns user_id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "plain_role_dept", can_manage_depts=False)
    user_id = _make_user(db, email, name="Plain User")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id


# ---------------------------------------------------------------------------
# GET /api/dept
# ---------------------------------------------------------------------------


def test_list_depts_returns_200(client, engine):
    """對應 T1"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_dept(db, "業務部", "SALES001")
    _make_dept(db, "IT部", "IT001")
    db.commit()
    db.close()

    resp = client.get("/api/dept", headers=_token(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    data = body["data"]
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["total"] >= 2


def test_list_depts_keyword_filter(client, engine):
    """對應 T2"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_dept(db, "業務一部", "SALES001A")
    _make_dept(db, "IT部", "IT002")
    db.commit()
    db.close()

    resp = client.get("/api/dept?keyword=業務", headers=_token(admin_id))
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    names = [i["name"] for i in items]
    assert any("業務" in n for n in names)
    assert "IT部" not in names


def test_list_depts_no_permission_returns_403(client, engine):
    """對應 T3"""
    user_id = _setup_plain_user(engine)

    resp = client.get("/api/dept", headers=_token(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_list_depts_unauthenticated_returns_401(client):
    """未登入應回 401"""
    resp = client.get("/api/dept")
    assert resp.status_code == 401


def test_list_depts_pagination(client, engine):
    """對應 T24"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    for i in range(30):
        _make_dept(db, f"部門{i:02d}", f"CODE{i:02d}")
    db.commit()
    db.close()

    resp = client.get("/api/dept?page=2&page_size=10", headers=_token(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["page"] == 2
    assert data["page_size"] == 10
    assert data["total"] == 30
    assert len(data["items"]) == 10


def test_list_depts_invalid_page_size_returns_400(client, engine):
    """對應 T25"""
    admin_id, _ = _setup_admin(engine)

    resp = client.get("/api/dept?page_size=7", headers=_token(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "每頁筆數僅允許 10、25 或 50"


def test_list_depts_page_zero_returns_400(client, engine):
    """對應 T26"""
    admin_id, _ = _setup_admin(engine)

    resp = client.get("/api/dept?page=0", headers=_token(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "頁碼不可小於 1"


# ---------------------------------------------------------------------------
# POST /api/dept
# ---------------------------------------------------------------------------


def test_create_dept_returns_201(client, engine):
    """對應 T4"""
    admin_id, _ = _setup_admin(engine)

    resp = client.post(
        "/api/dept",
        json={"name": "IT部門", "code": "IT001_NEW"},
        headers=_token(admin_id),
    )
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"


def test_create_dept_duplicate_code_returns_400(client, engine):
    """對應 T5"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_dept(db, "IT部", "IT001_DUP")
    db.commit()
    db.close()

    resp = client.post(
        "/api/dept",
        json={"name": "另一個IT部", "code": "IT001_DUP"},
        headers=_token(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "此部門代碼已被使用"


def test_create_dept_parent_at_level3_returns_400(client, engine):
    """對應 T6 - parent dept is at level 3"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    lvl1_id = _make_dept(db, "L1部門", "L1CODE")
    lvl2_id = _make_dept(db, "L2部門", "L2CODE", parent_id=lvl1_id)
    lvl3_id = _make_dept(db, "L3部門", "L3CODE", parent_id=lvl2_id)
    db.commit()
    db.close()

    resp = client.post(
        "/api/dept",
        json={"name": "L4部門", "code": "L4CODE", "parent_id": lvl3_id},
        headers=_token(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "部門層級最多 3 層，無法在此部門下新增子部門"


def test_create_dept_no_permission_returns_403(client, engine):
    """未授權新增應回 403"""
    user_id = _setup_plain_user(engine, "plain2@dept.com")

    resp = client.post(
        "/api/dept",
        json={"name": "部門X", "code": "X001"},
        headers=_token(user_id),
    )
    assert resp.status_code == 403


def test_create_dept_unauthenticated_returns_401(client):
    """未登入 POST 應回 401"""
    resp = client.post("/api/dept", json={"name": "部門X", "code": "X001"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /api/dept/{id}
# ---------------------------------------------------------------------------


def test_update_dept_returns_200(client, engine):
    """對應 T7"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    dept_id = _make_dept(db, "舊名稱部門", "UPDATE001")
    db.commit()
    db.close()

    resp = client.patch(
        f"/api/dept/{dept_id}",
        json={"name": "新名稱部門"},
        headers=_token(admin_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"


def test_update_dept_not_found_returns_404(client, engine):
    """對應 T8"""
    admin_id, _ = _setup_admin(engine)

    resp = client.patch(
        "/api/dept/99999",
        json={"name": "不存在部門"},
        headers=_token(admin_id),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "部門不存在"


def test_update_dept_duplicate_code_returns_400(client, engine):
    """對應 T9"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    dept_a_id = _make_dept(db, "部門A", "B001_TAKEN")
    dept_b_id = _make_dept(db, "部門B", "B002_TARGET")
    db.commit()
    db.close()

    resp = client.patch(
        f"/api/dept/{dept_b_id}",
        json={"code": "B001_TAKEN"},
        headers=_token(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "此部門代碼已被使用"


def test_update_dept_no_permission_returns_403(client, engine):
    """未授權編輯應回 403"""
    user_id = _setup_plain_user(engine, "plain3@dept.com")

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    dept_id = _make_dept(db, "部門C", "C001")
    db.commit()
    db.close()

    resp = client.patch(
        f"/api/dept/{dept_id}",
        json={"name": "新名稱"},
        headers=_token(user_id),
    )
    assert resp.status_code == 403


def test_update_dept_unauthenticated_returns_401(client):
    """未登入 PATCH 應回 401"""
    resp = client.patch("/api/dept/1", json={"name": "x"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /api/dept/{id}/toggle
# ---------------------------------------------------------------------------


def test_toggle_dept_disable_no_members_returns_200(client, engine):
    """對應 T10"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    dept_id = _make_dept(db, "空部門", "EMPTY001")
    db.commit()
    db.close()

    resp = client.patch(
        f"/api/dept/{dept_id}/toggle",
        json={"is_active": False},
        headers=_token(admin_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "停用成功"


def test_toggle_dept_disable_with_members_returns_400(client, engine):
    """對應 T11"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    dept_id = _make_dept(db, "有人員部門", "HASMEM001")
    _make_user(db, "member@dept.com", name="部門成員", dept_id=dept_id)
    db.commit()
    db.close()

    resp = client.patch(
        f"/api/dept/{dept_id}/toggle",
        json={"is_active": False},
        headers=_token(admin_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "此部門仍有人員，無法停用"


def test_toggle_dept_enable_returns_200(client, engine):
    """對應 T12"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    dept_id = _make_dept(db, "停用部門", "DISABLED001", is_active=False)
    db.commit()
    db.close()

    resp = client.patch(
        f"/api/dept/{dept_id}/toggle",
        json={"is_active": True},
        headers=_token(admin_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "啟用成功"


def test_toggle_dept_no_permission_returns_403(client, engine):
    """未授權 toggle 應回 403"""
    user_id = _setup_plain_user(engine, "plain4@dept.com")

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    dept_id = _make_dept(db, "部門D", "D001")
    db.commit()
    db.close()

    resp = client.patch(
        f"/api/dept/{dept_id}/toggle",
        json={"is_active": False},
        headers=_token(user_id),
    )
    assert resp.status_code == 403


def test_toggle_dept_unauthenticated_returns_401(client):
    """未登入 toggle 應回 401"""
    resp = client.patch("/api/dept/1/toggle", json={"is_active": False})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/dept/{id}/members
# ---------------------------------------------------------------------------


def test_get_dept_members_with_members_returns_200(client, engine):
    """對應 T13"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    dept_id = _make_dept(db, "有成員部門", "MEM001")
    _make_user(db, "m1@dept.com", name="成員一", dept_id=dept_id)
    _make_user(db, "m2@dept.com", name="成員二", dept_id=dept_id)
    db.commit()
    db.close()

    resp = client.get(f"/api/dept/{dept_id}/members", headers=_token(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert len(body["data"]) == 2
    names = [m["name"] for m in body["data"]]
    assert "成員一" in names
    assert "成員二" in names


def test_get_dept_members_empty_returns_200(client, engine):
    """對應 T14"""
    admin_id, _ = _setup_admin(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    dept_id = _make_dept(db, "空部門B", "EMPTY002")
    db.commit()
    db.close()

    resp = client.get(f"/api/dept/{dept_id}/members", headers=_token(admin_id))
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_get_dept_members_no_permission_returns_403(client, engine):
    """對應 T22"""
    user_id = _setup_plain_user(engine, "plain5@dept.com")

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    dept_id = _make_dept(db, "部門E", "E001")
    db.commit()
    db.close()

    resp = client.get(f"/api/dept/{dept_id}/members", headers=_token(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_get_dept_members_not_found_returns_404(client, engine):
    """對應 T23"""
    admin_id, _ = _setup_admin(engine)

    resp = client.get("/api/dept/99999/members", headers=_token(admin_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "部門不存在"


def test_get_dept_members_unauthenticated_returns_401(client):
    """未登入 GET members 應回 401"""
    resp = client.get("/api/dept/1/members")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/dept/options
# ---------------------------------------------------------------------------


def test_get_dept_options_returns_200(client, engine):
    """對應 T15"""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "options_role", can_manage_depts=False)
    user_id = _make_user(db, "options@dept.com")
    _assign_role(db, user_id, role_id)
    # depth 1
    lvl1_id = _make_dept(db, "一級部門", "OPT_L1")
    # depth 2
    lvl2_id = _make_dept(db, "二級部門", "OPT_L2", parent_id=lvl1_id)
    # depth 3 — should be excluded
    lvl3_id = _make_dept(db, "三級部門", "OPT_L3", parent_id=lvl2_id)
    db.commit()
    db.close()

    resp = client.get("/api/dept/options", headers=_token(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    ids = [d["id"] for d in body["data"]]
    assert lvl1_id in ids
    assert lvl2_id in ids
    assert lvl3_id not in ids


def test_get_dept_options_unauthenticated_returns_401(client):
    """對應 T16"""
    resp = client.get("/api/dept/options")
    assert resp.status_code == 401
