"""
fn_user API 整合測試
對應 _fn_user_test_api.md T1–T10
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.models.token_blacklist import TokenBlacklist
from app.db.models.user import Role, User, UserRole
from app.db.session import get_db
from app.main import app

# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def engine_user():
    _engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(bind=_engine, checkfirst=True)
    Role.__table__.create(bind=_engine, checkfirst=True)
    UserRole.__table__.create(bind=_engine, checkfirst=True)
    TokenBlacklist.__table__.create(bind=_engine, checkfirst=True)
    yield _engine
    UserRole.__table__.drop(bind=_engine, checkfirst=True)
    TokenBlacklist.__table__.drop(bind=_engine, checkfirst=True)
    User.__table__.drop(bind=_engine, checkfirst=True)
    Role.__table__.drop(bind=_engine, checkfirst=True)


@pytest.fixture(scope="function")
def db_session(engine_user):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine_user)
    db = Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client_user(engine_user):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_user)

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


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def _make_admin(db, email="admin@example.com", name="Admin") -> tuple[User, str]:
    """建立具有 can_manage_accounts 的管理員，回傳 (user, token)"""
    role = Role(name="admin", can_manage_accounts=True)
    db.add(role)
    db.flush()

    user = User(
        name=name,
        email=email,
        password_hash=hash_password("password123"),
        is_active=True,
    )
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return user, token


def _make_plain_user(db, email="plain@example.com", name="Plain") -> tuple[User, str]:
    """建立無管理權限的一般使用者，回傳 (user, token)"""
    role = Role(name="viewer", can_manage_accounts=False)
    db.add(role)
    db.flush()

    user = User(
        name=name,
        email=email,
        password_hash=hash_password("password123"),
        is_active=True,
    )
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return user, token


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ──────────────────────────────────────────────
# T1：查詢成功
# ──────────────────────────────────────────────


def test_list_users_returns_200(client_user, db_session):
    """對應 T1"""
    _, token = _make_admin(db_session)
    resp = client_user.get("/api/users", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    # 至少包含 admin 自己
    assert len(body["data"]) >= 1
    item = body["data"][0]
    assert "name" in item
    assert "email" in item
    assert "is_active" in item
    assert "roles" in item


# ──────────────────────────────────────────────
# T2：查詢無權限
# ──────────────────────────────────────────────


def test_list_users_no_permission_returns_403(client_user, db_session):
    """對應 T2"""
    _, token = _make_plain_user(db_session)
    resp = client_user.get("/api/users", headers=_auth_headers(token))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


# ──────────────────────────────────────────────
# T3：新增成功
# ──────────────────────────────────────────────


def test_create_user_returns_201(client_user, db_session):
    """對應 T3"""
    admin, token = _make_admin(db_session)
    role = db_session.query(Role).filter(Role.name == "admin").first()
    payload = {
        "name": "New User",
        "email": "newuser@example.com",
        "password": "securepass",
        "role_ids": [role.id],
    }
    resp = client_user.post("/api/users", json=payload, headers=_auth_headers(token))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"


# ──────────────────────────────────────────────
# T4：新增 Email 重複
# ──────────────────────────────────────────────


def test_create_user_duplicate_email_returns_400(client_user, db_session):
    """對應 T4"""
    admin, token = _make_admin(db_session)
    role = db_session.query(Role).filter(Role.name == "admin").first()
    payload = {
        "name": "Dup User",
        "email": admin.email,  # 使用已存在的 email
        "password": "securepass",
        "role_ids": [role.id],
    }
    resp = client_user.post("/api/users", json=payload, headers=_auth_headers(token))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "此 Email 已被使用"


# ──────────────────────────────────────────────
# T5：新增密碼不足
# ──────────────────────────────────────────────


def test_create_user_short_password_returns_400(client_user, db_session):
    """對應 T5"""
    admin, token = _make_admin(db_session)
    role = db_session.query(Role).filter(Role.name == "admin").first()
    payload = {
        "name": "Short Pass",
        "email": "shortpass@example.com",
        "password": "1234567",  # 7 字元
        "role_ids": [role.id],
    }
    resp = client_user.post("/api/users", json=payload, headers=_auth_headers(token))
    assert resp.status_code == 422
    errors = resp.json()["detail"]
    assert any("密碼最少 8 字元" in str(e) for e in errors)


# ──────────────────────────────────────────────
# T6：新增角色為空
# ──────────────────────────────────────────────


def test_create_user_empty_roles_returns_400(client_user, db_session):
    """對應 T6"""
    _, token = _make_admin(db_session)
    payload = {
        "name": "No Role",
        "email": "norole@example.com",
        "password": "securepass",
        "role_ids": [],
    }
    resp = client_user.post("/api/users", json=payload, headers=_auth_headers(token))
    assert resp.status_code == 422
    errors = resp.json()["detail"]
    assert any("角色未設定" in str(e) for e in errors)


# ──────────────────────────────────────────────
# T7：修改成功
# ──────────────────────────────────────────────


def test_update_user_returns_200(client_user, db_session):
    """對應 T7"""
    admin, token = _make_admin(db_session)
    role = db_session.query(Role).filter(Role.name == "admin").first()

    # 先建立目標使用者
    target = User(
        name="Target User",
        email="target@example.com",
        password_hash=hash_password("password123"),
        is_active=True,
    )
    db_session.add(target)
    db_session.flush()
    db_session.add(UserRole(user_id=target.id, role_id=role.id))
    db_session.commit()

    payload = {"name": "Updated Name"}
    resp = client_user.patch(
        f"/api/users/{target.email}",
        json=payload,
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"


# ──────────────────────────────────────────────
# T8：修改使用者不存在
# ──────────────────────────────────────────────


def test_update_user_not_found_returns_404(client_user, db_session):
    """對應 T8"""
    _, token = _make_admin(db_session)
    resp = client_user.patch(
        "/api/users/notexist@example.com",
        json={"name": "Any Name"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "使用者不存在"


# ──────────────────────────────────────────────
# T9：刪除成功
# ──────────────────────────────────────────────


def test_delete_user_returns_200(client_user, db_session):
    """對應 T9"""
    admin, token = _make_admin(db_session)
    role = db_session.query(Role).filter(Role.name == "admin").first()

    # 建立要刪除的使用者
    target = User(
        name="To Delete",
        email="todelete@example.com",
        password_hash=hash_password("password123"),
        is_active=True,
    )
    db_session.add(target)
    db_session.flush()
    db_session.add(UserRole(user_id=target.id, role_id=role.id))
    db_session.commit()

    resp = client_user.delete(
        f"/api/users/{target.email}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    # 確認資料庫已移除
    deleted = db_session.query(User).filter(User.email == target.email).first()
    assert deleted is None

    user_roles = db_session.query(UserRole).filter(UserRole.user_id == target.id).all()
    assert user_roles == []


# ──────────────────────────────────────────────
# T10：刪除自己
# ──────────────────────────────────────────────


def test_delete_self_returns_400(client_user, db_session):
    """對應 T10"""
    admin, token = _make_admin(db_session)
    resp = client_user.delete(
        f"/api/users/{admin.email}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "無法刪除自己的帳號"


# ──────────────────────────────────────────────
# 額外：無 JWT 時回 401
# ──────────────────────────────────────────────


def test_list_users_no_token_returns_401(client_user):
    """未帶 JWT Token 呼叫，回 401（HTTPBearer 預設）"""
    resp = client_user.get("/api/users")
    assert resp.status_code == 401
