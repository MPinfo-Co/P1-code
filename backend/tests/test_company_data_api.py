"""
Tests for fn_company_data APIs:
  GET    /company-data
  POST   /company-data
  PATCH  /company-data/{id}
  DELETE /company-data/{id}
  GET    /company-data/partner-options
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.connector import get_db
from app.db.models.fn_company_data import AiPartner, CompanyData, PartnerCompanyData
from app.db.models.function_access import FunctionFolder, FunctionItems, RoleFunction
from app.db.models.user_role import Role, TokenBlacklist, User, UserRole
from app.main import app
from app.utils.util_store import create_access_token, hash_password

TEST_DATABASE_URL = "sqlite:///:memory:"

_SEED_TABLES = [
    User.__table__,
    Role.__table__,
    UserRole.__table__,
    TokenBlacklist.__table__,
    FunctionFolder.__table__,
    FunctionItems.__table__,
    RoleFunction.__table__,
    AiPartner.__table__,
    CompanyData.__table__,
    PartnerCompanyData.__table__,
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
# Helpers
# ---------------------------------------------------------------------------


def _make_user(db: Session, email: str, name: str = "Test User") -> int:
    user = User(name=name, email=email, password_hash=hash_password("password123"))
    db.add(user)
    db.flush()
    return user.id


def _make_role(db: Session, name: str) -> int:
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _make_folder(db: Session, code: str = "設定") -> int:
    folder = FunctionFolder(
        folder_code=code, folder_label=code, default_open=False, sort_order=1
    )
    db.add(folder)
    db.flush()
    return folder.id


def _make_function(db: Session, code: str, folder_id: int) -> int:
    fn = FunctionItems(
        function_code=code, function_label=code, folder_id=folder_id, sort_order=1
    )
    db.add(fn)
    db.flush()
    return fn.function_id


def _grant_function(db: Session, role_id: int, function_id: int) -> None:
    db.add(RoleFunction(role_id=role_id, function_id=function_id))
    db.flush()


def _make_partner(db: Session, name: str, is_enabled: bool = True) -> int:
    partner = AiPartner(name=name, is_enabled=is_enabled)
    db.add(partner)
    db.flush()
    return partner.id


def _make_company_data(db: Session, name: str, content: str) -> int:
    record = CompanyData(name=name, content=content)
    db.add(record)
    db.flush()
    return record.id


def _link_partner(db: Session, company_data_id: int, partner_id: int) -> None:
    db.add(PartnerCompanyData(company_data_id=company_data_id, partner_id=partner_id))
    db.flush()


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _setup_user_with_permission(engine) -> tuple[int, int]:
    """建立具備 fn_company_data 權限的使用者。回傳 (user_id, fn_id)。"""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_folder(db, "AI 夥伴")
    fn_id = _make_function(db, "fn_company_data", folder_id)
    role_id = _make_role(db, "admin")
    user_id = _make_user(db, "admin@test.com", "Admin")
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_id)
    db.commit()
    db.close()
    return user_id, fn_id


def _setup_user_without_permission(engine) -> int:
    """建立不具備 fn_company_data 權限的使用者。回傳 user_id。"""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "plain_role")
    user_id = _make_user(db, "plain@test.com", "Plain User")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id


# ---------------------------------------------------------------------------
# GET /company-data — T1, T2, T3
# ---------------------------------------------------------------------------


def test_list_company_data_returns_200(client, engine):
    """對應 T1"""
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "GeminiPro")
    cd_id = _make_company_data(db, "公司網段", "192.168.1.0/24")
    _link_partner(db, cd_id, partner_id)
    _make_company_data(db, "資安規則", "禁止使用未加密協定")
    db.commit()
    db.close()

    resp = client.get("/company-data", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    data = body["data"]
    assert isinstance(data, list)
    assert len(data) == 2

    # Verify structure
    cd_item = next(d for d in data if d["name"] == "公司網段")
    assert "id" in cd_item
    assert cd_item["content"] == "192.168.1.0/24"
    assert isinstance(cd_item["partners"], list)
    assert len(cd_item["partners"]) == 1
    assert cd_item["partners"][0]["name"] == "GeminiPro"


def test_list_company_data_keyword_filter(client, engine):
    """對應 T2"""
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "網段分析夥伴")
    cd1_id = _make_company_data(db, "公司網段", "192.168.1.0/24")
    _link_partner(db, cd1_id, partner_id)
    # 資安規則 也連結到「網段分析夥伴」，讓 partner name 過濾可命中
    cd2_id = _make_company_data(db, "資安規則", "禁止使用未加密協定")
    _link_partner(db, cd2_id, partner_id)
    _make_company_data(db, "其他規定", "其他內容")
    db.commit()
    db.close()

    resp = client.get("/company-data?keyword=網段", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    names = [d["name"] for d in data]
    # "公司網段" matches by name; "資安規則" matches via partner "網段分析夥伴"
    assert "公司網段" in names
    assert "資安規則" in names
    # "其他規定" should NOT match
    assert "其他規定" not in names

    # Keyword that matches only one by content
    resp2 = client.get("/company-data?keyword=加密", headers=_auth_headers(user_id))
    data2 = resp2.json()["data"]
    names2 = [d["name"] for d in data2]
    assert "資安規則" in names2
    assert "公司網段" not in names2
    assert "其他規定" not in names2


def test_list_company_data_no_permission_returns_403(client, engine):
    """對應 T3"""
    user_id = _setup_user_without_permission(engine)

    resp = client.get("/company-data", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_list_company_data_unauthenticated_returns_401(client, engine):
    """未登入 GET /company-data 應回 401"""
    resp = client.get("/company-data")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /company-data — T4, T5, T6, T10
# ---------------------------------------------------------------------------


def test_create_company_data_returns_201(client, engine):
    """對應 T4"""
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "GeminiPartner")
    db.commit()
    db.close()

    payload = {
        "name": "公司網段",
        "content": "192.168.1.0/24",
        "partner_ids": [partner_id],
    }
    resp = client.post("/company-data", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"

    # Verify DB records
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    record = db.query(CompanyData).filter(CompanyData.name == "公司網段").first()
    assert record is not None
    links = (
        db.query(PartnerCompanyData)
        .filter(PartnerCompanyData.company_data_id == record.id)
        .all()
    )
    assert len(links) == 1
    assert links[0].partner_id == partner_id
    db.close()


def test_create_company_data_empty_name_returns_400(client, engine):
    """對應 T5"""
    user_id, _ = _setup_user_with_permission(engine)

    payload = {"name": "", "content": "some content", "partner_ids": []}
    resp = client.post("/company-data", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "資料名稱不可為空"


def test_create_company_data_empty_content_returns_400(client, engine):
    """對應 T6"""
    user_id, _ = _setup_user_with_permission(engine)

    payload = {"name": "公司網段", "content": "", "partner_ids": []}
    resp = client.post("/company-data", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "內容不可為空"


def test_create_company_data_duplicate_name_returns_409(client, engine):
    """對應 T10"""
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_company_data(db, "公司網段", "existing content")
    db.commit()
    db.close()

    payload = {"name": "公司網段", "content": "different content", "partner_ids": []}
    resp = client.post("/company-data", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 409
    assert resp.json()["detail"] == "資料名稱已存在"


def test_create_company_data_no_permission_returns_403(client, engine):
    """無權限 POST /company-data 應回 403"""
    user_id = _setup_user_without_permission(engine)

    payload = {"name": "test", "content": "test content", "partner_ids": []}
    resp = client.post("/company-data", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /company-data/{id} — T7
# ---------------------------------------------------------------------------


def test_update_company_data_returns_200(client, engine):
    """對應 T7"""
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "GeminiPartner")
    cd_id = _make_company_data(db, "原始名稱", "原始內容")
    _link_partner(db, cd_id, partner_id)
    partner2_id = _make_partner(db, "ClaudePartner")
    db.commit()
    db.close()

    payload = {
        "name": "更新後名稱",
        "content": "更新後內容",
        "partner_ids": [partner2_id],
    }
    resp = client.patch(
        f"/company-data/{cd_id}", json=payload, headers=_auth_headers(user_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    # Verify DB state
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    record = db.get(CompanyData, cd_id)
    assert record.name == "更新後名稱"
    assert record.content == "更新後內容"
    links = (
        db.query(PartnerCompanyData)
        .filter(PartnerCompanyData.company_data_id == cd_id)
        .all()
    )
    assert len(links) == 1
    assert links[0].partner_id == partner2_id
    db.close()


def test_update_company_data_not_found_returns_404(client, engine):
    """修改不存在的 id 應回 404"""
    user_id, _ = _setup_user_with_permission(engine)

    payload = {"name": "新名稱", "content": "新內容", "partner_ids": []}
    resp = client.patch(
        "/company-data/99999", json=payload, headers=_auth_headers(user_id)
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "資料不存在"


def test_update_company_data_duplicate_name_returns_409(client, engine):
    """修改 name 與其他筆資料重複應回 409"""
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_company_data(db, "名稱A", "content A")
    cd_id = _make_company_data(db, "名稱B", "content B")
    db.commit()
    db.close()

    payload = {"name": "名稱A", "content": "updated content", "partner_ids": []}
    resp = client.patch(
        f"/company-data/{cd_id}", json=payload, headers=_auth_headers(user_id)
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "資料名稱已存在"


def test_update_company_data_no_permission_returns_403(client, engine):
    """無權限 PATCH /company-data/{id} 應回 403"""
    user_id = _setup_user_without_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    cd_id = _make_company_data(db, "test name", "test content")
    db.commit()
    db.close()

    payload = {"name": "new name", "content": "new content", "partner_ids": []}
    resp = client.patch(
        f"/company-data/{cd_id}", json=payload, headers=_auth_headers(user_id)
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /company-data/{id} — T8
# ---------------------------------------------------------------------------


def test_delete_company_data_returns_200(client, engine):
    """對應 T8"""
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "GeminiPartner")
    cd_id = _make_company_data(db, "待刪資料", "待刪內容")
    _link_partner(db, cd_id, partner_id)
    db.commit()
    db.close()

    resp = client.delete(f"/company-data/{cd_id}", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    # Verify DB records are gone
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    assert db.get(CompanyData, cd_id) is None
    links = (
        db.query(PartnerCompanyData)
        .filter(PartnerCompanyData.company_data_id == cd_id)
        .all()
    )
    assert len(links) == 0
    db.close()


def test_delete_company_data_not_found_returns_404(client, engine):
    """刪除不存在的 id 應回 404"""
    user_id, _ = _setup_user_with_permission(engine)

    resp = client.delete("/company-data/99999", headers=_auth_headers(user_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "資料不存在"


def test_delete_company_data_no_permission_returns_403(client, engine):
    """無權限 DELETE /company-data/{id} 應回 403"""
    user_id = _setup_user_without_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    cd_id = _make_company_data(db, "test name", "test content")
    db.commit()
    db.close()

    resp = client.delete(f"/company-data/{cd_id}", headers=_auth_headers(user_id))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /company-data/partner-options — T9
# ---------------------------------------------------------------------------


def test_list_partner_options_returns_200(client, engine):
    """對應 T9"""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    user_id = _make_user(db, "any@test.com", "Any User")
    _make_partner(db, "GeminiPro", is_enabled=True)
    _make_partner(db, "Claude", is_enabled=True)
    _make_partner(db, "DisabledPartner", is_enabled=False)
    db.commit()
    db.close()

    resp = client.get("/company-data/partner-options", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    data = body["data"]
    assert isinstance(data, list)
    names = [d["name"] for d in data]
    assert "GeminiPro" in names
    assert "Claude" in names
    # Disabled partner must NOT be included
    assert "DisabledPartner" not in names
    # Must have id and name fields
    assert all("id" in d and "name" in d for d in data)


def test_list_partner_options_unauthenticated_returns_401(client, engine):
    """未登入 GET /company-data/partner-options 應回 401"""
    resp = client.get("/company-data/partner-options")
    assert resp.status_code == 401


def test_list_partner_options_sorted_by_name(client, engine):
    """partner-options 回傳依 name 升冪排序"""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    user_id = _make_user(db, "sort@test.com", "Sort User")
    _make_partner(db, "Zebra Partner", is_enabled=True)
    _make_partner(db, "Alpha Partner", is_enabled=True)
    _make_partner(db, "Middle Partner", is_enabled=True)
    db.commit()
    db.close()

    resp = client.get("/company-data/partner-options", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    names = [d["name"] for d in data]
    assert names == sorted(names)
