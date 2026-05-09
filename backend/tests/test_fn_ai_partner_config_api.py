"""
Tests for fn_ai_partner_config APIs:
  GET    /ai-partner-config
  POST   /ai-partner-config
  PATCH  /ai-partner-config/{id}
  DELETE /ai-partner-config/{id}

And fn_tool_options:
  GET    /tool/options
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest")
os.environ.setdefault("AES_KEY", "test-aes-256-key-for-pytest-12345")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.connector import get_db
from app.main import app
from app.db.models.fn_ai_partner_config import AiPartner, AiPartnerTool
from app.db.models.fn_tool import Tool, ToolBodyParam
from app.db.models.function_access import (
    FunctionItems as Function,
    FunctionFolder,
    RoleFunction,
)
from app.db.models.user_role import Role, TokenBlacklist, User, UserRole
from app.utils.util_store import create_access_token, hash_password

TEST_DATABASE_URL = "sqlite:///:memory:"

_SEED_TABLES = [
    User.__table__,
    Role.__table__,
    UserRole.__table__,
    TokenBlacklist.__table__,
    FunctionFolder.__table__,
    Function.__table__,
    RoleFunction.__table__,
    Tool.__table__,
    ToolBodyParam.__table__,
    AiPartner.__table__,
    AiPartnerTool.__table__,
]


@pytest.fixture(scope="function")
def engine():
    _engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    for table in _SEED_TABLES:
        table.create(bind=_engine, checkfirst=True)
    yield _engine
    for table in reversed(_SEED_TABLES):
        table.drop(bind=_engine, checkfirst=True)


@pytest.fixture(scope="function")
def client(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_function_folder(db: Session, name: str = "AI夥伴", sort_order: int = 1) -> int:
    folder = FunctionFolder(
        folder_code=name, folder_label=name, sort_order=sort_order
    )
    db.add(folder)
    db.flush()
    return folder.id


def _make_function(db: Session, code: str, folder_id: int, sort_order: int = 1) -> int:
    fn = Function(
        function_code=code,
        function_label=code,
        folder_id=folder_id,
        sort_order=sort_order,
    )
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


def _setup_admin(engine):
    """Create admin user with fn_ai_partner_config permission. Return (user_id, role_id, fn_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_function_folder(db, "AI夥伴", 1)
    fn_id = _make_function(db, "fn_ai_partner_config", folder_id, 2)
    role_id = _make_role(db, "admin")
    user_id = _make_user(db, "admin@test.com", name="Admin User")
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_id


def _setup_plain_user(engine, email: str = "plain@test.com"):
    """Create a user without fn_ai_partner_config permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "plain_role")
    user_id = _make_user(db, email, name="Plain User")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id, role_id


def _add_partner(
    engine,
    name: str,
    description: str | None = None,
    is_builtin: bool = False,
    is_enabled: bool = True,
) -> int:
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner = AiPartner(
        name=name,
        description=description,
        is_builtin=is_builtin,
        is_enabled=is_enabled,
    )
    db.add(partner)
    db.commit()
    pid = partner.id
    db.close()
    return pid


def _add_tool(engine, name: str) -> int:
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = Tool(
        name=name,
        endpoint_url="https://example.com/api",
        http_method="GET",
        auth_type="none",
    )
    db.add(tool)
    db.commit()
    tid = tool.id
    db.close()
    return tid


# ---------------------------------------------------------------------------
# GET /ai-partner-config — T1, T2, T3
# ---------------------------------------------------------------------------


def test_list_ai_partners_returns_200(client, engine):
    """對應 T1"""
    admin_id, _, _ = _setup_admin(engine)
    tool_id = _add_tool(engine, "Tool Alpha")
    partner_id = _add_partner(engine, "客服小幫手", description="處理客服問題")

    # Link tool to partner
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    db.add(AiPartnerTool(partner_id=partner_id, tool_id=tool_id))
    db.commit()
    db.close()

    resp = client.get("/ai-partner-config", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1

    item = next(d for d in body["data"] if d["name"] == "客服小幫手")
    assert "id" in item
    assert item["name"] == "客服小幫手"
    assert item["description"] == "處理客服問題"
    assert "is_enabled" in item
    assert "role_definition" in item
    assert "behavior_limit" in item
    assert isinstance(item["tool_ids"], list)
    assert tool_id in item["tool_ids"]


def test_list_ai_partners_keyword_filter(client, engine):
    """對應 T2"""
    admin_id, _, _ = _setup_admin(engine)
    _add_partner(engine, "客服機器人", description="專業客服助理")
    _add_partner(engine, "資安分析師", description="分析安全事件")

    resp = client.get(
        "/ai-partner-config?keyword=客服", headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    names = [d["name"] for d in data]
    assert "客服機器人" in names
    assert "資安分析師" not in names


def test_list_ai_partners_no_permission_returns_403(client, engine):
    """對應 T3"""
    user_id, _ = _setup_plain_user(engine)

    resp = client.get("/ai-partner-config", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


# ---------------------------------------------------------------------------
# POST /ai-partner-config — T4, T5, T6
# ---------------------------------------------------------------------------


def test_add_ai_partner_returns_201(client, engine):
    """對應 T4"""
    admin_id, _, _ = _setup_admin(engine)
    tool_id = _add_tool(engine, "Tool Beta")

    payload = {
        "name": "新夥伴",
        "description": "描述文字",
        "role_definition": "你是一位客服專家",
        "behavior_limit": "不討論競品",
        "tool_ids": [tool_id],
    }
    resp = client.post(
        "/ai-partner-config", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"

    # Verify DB records
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner = db.query(AiPartner).filter(AiPartner.name == "新夥伴").first()
    assert partner is not None
    assert partner.is_enabled is True
    assert partner.is_builtin is False
    links = db.query(AiPartnerTool).filter(AiPartnerTool.partner_id == partner.id).all()
    assert len(links) == 1
    assert links[0].tool_id == tool_id
    db.close()


def test_add_ai_partner_empty_name_returns_400(client, engine):
    """對應 T5"""
    admin_id, _, _ = _setup_admin(engine)

    payload = {"name": "", "tool_ids": []}
    resp = client.post(
        "/ai-partner-config", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "夥伴名稱為必填"


def test_add_ai_partner_duplicate_name_returns_400(client, engine):
    """對應 T6"""
    admin_id, _, _ = _setup_admin(engine)
    _add_partner(engine, "重複名稱夥伴")

    payload = {"name": "重複名稱夥伴", "tool_ids": []}
    resp = client.post(
        "/ai-partner-config", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "夥伴名稱已存在"


# ---------------------------------------------------------------------------
# PATCH /ai-partner-config/{id} — T7, T8, T9
# ---------------------------------------------------------------------------


def test_update_ai_partner_returns_200(client, engine):
    """對應 T7"""
    admin_id, _, _ = _setup_admin(engine)
    partner_id = _add_partner(engine, "舊名稱")
    tool_id = _add_tool(engine, "Tool Gamma")

    payload = {
        "name": "新名稱",
        "description": "更新描述",
        "role_definition": "新角色定義",
        "behavior_limit": "新行為限制",
        "tool_ids": [tool_id],
        "is_enabled": True,
    }
    resp = client.patch(
        f"/ai-partner-config/{partner_id}",
        json=payload,
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    # Verify tools updated
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    links = (
        db.query(AiPartnerTool)
        .filter(AiPartnerTool.partner_id == partner_id)
        .all()
    )
    assert len(links) == 1
    assert links[0].tool_id == tool_id
    db.close()


def test_update_ai_partner_disable_returns_200(client, engine):
    """對應 T8"""
    admin_id, _, _ = _setup_admin(engine)
    partner_id = _add_partner(engine, "啟用夥伴", is_enabled=True)

    payload = {
        "name": "啟用夥伴",
        "tool_ids": [],
        "is_enabled": False,
    }
    resp = client.patch(
        f"/ai-partner-config/{partner_id}",
        json=payload,
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner = db.query(AiPartner).filter(AiPartner.id == partner_id).first()
    assert partner.is_enabled is False
    db.close()


def test_update_ai_partner_not_found_returns_404(client, engine):
    """對應 T9"""
    admin_id, _, _ = _setup_admin(engine)

    payload = {"name": "任意名稱", "tool_ids": []}
    resp = client.patch(
        "/ai-partner-config/99999",
        json=payload,
        headers=_auth_headers(admin_id),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "AI 夥伴不存在"


# ---------------------------------------------------------------------------
# DELETE /ai-partner-config/{id} — T10, T11, T12
# ---------------------------------------------------------------------------


def test_delete_ai_partner_returns_200(client, engine):
    """對應 T10"""
    admin_id, _, _ = _setup_admin(engine)
    tool_id = _add_tool(engine, "Tool Delta")
    partner_id = _add_partner(engine, "待刪除夥伴")

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    db.add(AiPartnerTool(partner_id=partner_id, tool_id=tool_id))
    db.commit()
    db.close()

    resp = client.delete(
        f"/ai-partner-config/{partner_id}", headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    db = Session_()
    assert db.query(AiPartner).filter(AiPartner.id == partner_id).first() is None
    assert (
        db.query(AiPartnerTool)
        .filter(AiPartnerTool.partner_id == partner_id)
        .count()
        == 0
    )
    db.close()


def test_delete_builtin_ai_partner_returns_400(client, engine):
    """對應 T11"""
    admin_id, _, _ = _setup_admin(engine)
    partner_id = _add_partner(engine, "內建夥伴", is_builtin=True)

    resp = client.delete(
        f"/ai-partner-config/{partner_id}", headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "內建夥伴不可刪除"


def test_delete_ai_partner_not_found_returns_404(client, engine):
    """對應 T12"""
    admin_id, _, _ = _setup_admin(engine)

    resp = client.delete(
        "/ai-partner-config/99999", headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "AI 夥伴不存在"


# ---------------------------------------------------------------------------
# GET /tool/options — T13, T14
# ---------------------------------------------------------------------------


def test_list_tool_options_returns_200(client, engine):
    """對應 T13"""
    admin_id, _, _ = _setup_admin(engine)
    _add_tool(engine, "Ztool")
    _add_tool(engine, "Atool")

    resp = client.get("/tool/options", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 2

    # Verify fields: id, name, description
    for item in body["data"]:
        assert "id" in item
        assert "name" in item
        assert "description" in item

    # Verify ascending name order
    names = [d["name"] for d in body["data"]]
    assert names == sorted(names)


def test_list_tool_options_unauthenticated_returns_401(client, engine):
    """對應 T14"""
    resp = client.get("/tool/options")
    assert resp.status_code == 401
