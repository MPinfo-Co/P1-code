"""
Tests for fn_company_data APIs:
  GET    /company-data
  POST   /company-data
  PATCH  /company-data/{id}
  DELETE /company-data/{id}
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
from app.db.models.fn_company_data import CompanyData
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
    CompanyData.__table__,
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


def _make_folder(db: Session, code: str = "資安專家") -> int:
    folder = FunctionFolder(
        folder_code=code, folder_label=code, sort_order=1
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


def _make_company_data(db: Session, name: str, content: str) -> int:
    record = CompanyData(name=name, content=content)
    db.add(record)
    db.flush()
    return record.id


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _setup_user_with_permission(engine) -> tuple[int, int]:
    """建立具備 fn_company_data 權限的使用者。回傳 (user_id, fn_id)。"""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_folder(db, "資安專家")
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
# GET /company-data
# ---------------------------------------------------------------------------


def test_list_company_data_returns_200(client, engine):
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_company_data(db, "公司網段", "192.168.1.0/24")
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
    names = [d["name"] for d in data]
    assert "公司網段" in names
    assert "資安規則" in names


def test_list_company_data_keyword_filter(client, engine):
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_company_data(db, "公司網段", "192.168.1.0/24")
    _make_company_data(db, "資安規則", "禁止使用未加密協定")
    _make_company_data(db, "其他規定", "其他內容")
    db.commit()
    db.close()

    # name match
    resp = client.get("/company-data?keyword=網段", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    names = [d["name"] for d in resp.json()["data"]]
    assert "公司網段" in names
    assert "資安規則" not in names

    # content match
    resp2 = client.get("/company-data?keyword=加密", headers=_auth_headers(user_id))
    names2 = [d["name"] for d in resp2.json()["data"]]
    assert "資安規則" in names2
    assert "公司網段" not in names2


def test_list_company_data_no_permission_returns_403(client, engine):
    user_id = _setup_user_without_permission(engine)

    resp = client.get("/company-data", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_list_company_data_unauthenticated_returns_401(client, engine):
    resp = client.get("/company-data")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /company-data
# ---------------------------------------------------------------------------


def test_create_company_data_returns_201(client, engine):
    user_id, _ = _setup_user_with_permission(engine)

    payload = {"name": "公司網段", "content": "192.168.1.0/24"}
    resp = client.post("/company-data", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    record = db.query(CompanyData).filter(CompanyData.name == "公司網段").first()
    assert record is not None
    assert record.content == "192.168.1.0/24"
    db.close()


def test_create_company_data_empty_name_returns_400(client, engine):
    user_id, _ = _setup_user_with_permission(engine)

    payload = {"name": "", "content": "some content"}
    resp = client.post("/company-data", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "資料名稱不可為空"


def test_create_company_data_empty_content_returns_400(client, engine):
    user_id, _ = _setup_user_with_permission(engine)

    payload = {"name": "公司網段", "content": ""}
    resp = client.post("/company-data", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "內容不可為空"


def test_create_company_data_duplicate_name_returns_409(client, engine):
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_company_data(db, "公司網段", "existing content")
    db.commit()
    db.close()

    payload = {"name": "公司網段", "content": "different content"}
    resp = client.post("/company-data", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 409
    assert resp.json()["detail"] == "資料名稱已存在"


def test_create_company_data_no_permission_returns_403(client, engine):
    user_id = _setup_user_without_permission(engine)

    payload = {"name": "test", "content": "test content"}
    resp = client.post("/company-data", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /company-data/{id}
# ---------------------------------------------------------------------------


def test_update_company_data_returns_200(client, engine):
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    cd_id = _make_company_data(db, "原始名稱", "原始內容")
    db.commit()
    db.close()

    payload = {"name": "更新後名稱", "content": "更新後內容"}
    resp = client.patch(
        f"/company-data/{cd_id}", json=payload, headers=_auth_headers(user_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    record = db.get(CompanyData, cd_id)
    assert record.name == "更新後名稱"
    assert record.content == "更新後內容"
    db.close()


def test_update_company_data_not_found_returns_404(client, engine):
    user_id, _ = _setup_user_with_permission(engine)

    payload = {"name": "新名稱", "content": "新內容"}
    resp = client.patch(
        "/company-data/99999", json=payload, headers=_auth_headers(user_id)
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "資料不存在"


def test_update_company_data_duplicate_name_returns_409(client, engine):
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_company_data(db, "名稱A", "content A")
    cd_id = _make_company_data(db, "名稱B", "content B")
    db.commit()
    db.close()

    payload = {"name": "名稱A", "content": "updated content"}
    resp = client.patch(
        f"/company-data/{cd_id}", json=payload, headers=_auth_headers(user_id)
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "資料名稱已存在"


def test_update_company_data_no_permission_returns_403(client, engine):
    user_id = _setup_user_without_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    cd_id = _make_company_data(db, "test name", "test content")
    db.commit()
    db.close()

    payload = {"name": "new name", "content": "new content"}
    resp = client.patch(
        f"/company-data/{cd_id}", json=payload, headers=_auth_headers(user_id)
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /company-data/{id}
# ---------------------------------------------------------------------------


def test_delete_company_data_returns_200(client, engine):
    user_id, _ = _setup_user_with_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    cd_id = _make_company_data(db, "待刪資料", "待刪內容")
    db.commit()
    db.close()

    resp = client.delete(f"/company-data/{cd_id}", headers=_auth_headers(user_id))
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    assert db.get(CompanyData, cd_id) is None
    db.close()


def test_delete_company_data_not_found_returns_404(client, engine):
    user_id, _ = _setup_user_with_permission(engine)

    resp = client.delete("/company-data/99999", headers=_auth_headers(user_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "資料不存在"


def test_delete_company_data_no_permission_returns_403(client, engine):
    user_id = _setup_user_without_permission(engine)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    cd_id = _make_company_data(db, "test name", "test content")
    db.commit()
    db.close()

    resp = client.delete(f"/company-data/{cd_id}", headers=_auth_headers(user_id))
    assert resp.status_code == 403
