"""
Tests for fn_feedback APIs:
  POST /feedback  (fn_feedback_submit_api)
  GET  /feedback  (fn_feedback_list_api)

Test IDs follow _fn_feedback_test_api.md: T1–T12.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest")

from sqlalchemy.orm import Session

from app.db.models.fn_feedback import Feedback
from app.db.models.function_access import FunctionFolder, FunctionItems, RoleFunction
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_user(db: Session, user_id: int, name: str, email: str) -> User:
    u = User(
        id=user_id,
        name=name,
        email=email,
        password_hash=hash_password("pw"),
    )
    db.add(u)
    db.flush()
    return u


def _seed_role(db: Session, role_id: int, name: str) -> Role:
    r = Role(id=role_id, name=name)
    db.add(r)
    db.flush()
    return r


def _seed_user_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _seed_fn_feedback_permission(db: Session, role_id: int) -> None:
    """Seed fn_feedback function item and grant to role."""
    folder = FunctionFolder(
        id=99, folder_code="fn_feedback_folder", folder_label="回饋", sort_order=99
    )
    db.add(folder)
    db.flush()
    fn = FunctionItems(
        function_id=99,
        function_code="fn_feedback",
        function_label="回饋管理",
        folder_id=99,
        sort_order=0,
    )
    db.add(fn)
    db.flush()
    db.add(RoleFunction(role_id=role_id, function_id=99))
    db.flush()


def _auth_header(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# POST /feedback
# ---------------------------------------------------------------------------


def test_T1_submit_feedback_with_comment(client):
    """T1: 提交回饋成功（含留言）"""
    db_gen = client.app.dependency_overrides[
        __import__("app.db.connector", fromlist=["get_db"]).get_db
    ]()
    db = next(db_gen)
    _seed_user(db, 1, "Alice", "alice@example.com")
    db.commit()
    db.close()

    resp = client.post(
        "/feedback",
        json={"rating": 5, "comment": "很好用"},
        headers=_auth_header(1),
    )
    assert resp.status_code == 201
    assert resp.json()["message"] == "回饋提交成功"


def test_T2_submit_feedback_missing_rating(client):
    """T2: 提交回饋缺少 rating"""
    db_gen = client.app.dependency_overrides[
        __import__("app.db.connector", fromlist=["get_db"]).get_db
    ]()
    db = next(db_gen)
    _seed_user(db, 2, "Bob", "bob@example.com")
    db.commit()
    db.close()

    resp = client.post(
        "/feedback",
        json={"comment": "很好用"},
        headers=_auth_header(2),
    )
    assert resp.status_code == 422


def test_T3_submit_feedback_rating_zero(client):
    """T3: 提交回饋 rating=0（超出下限）"""
    db_gen = client.app.dependency_overrides[
        __import__("app.db.connector", fromlist=["get_db"]).get_db
    ]()
    db = next(db_gen)
    _seed_user(db, 3, "Carol", "carol@example.com")
    db.commit()
    db.close()

    resp = client.post(
        "/feedback",
        json={"rating": 0},
        headers=_auth_header(3),
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "rating 須介於 1 至 5 之間"


def test_T4_submit_feedback_rating_six(client):
    """T4: 提交回饋 rating=6（超出上限）"""
    db_gen = client.app.dependency_overrides[
        __import__("app.db.connector", fromlist=["get_db"]).get_db
    ]()
    db = next(db_gen)
    _seed_user(db, 4, "Dave", "dave@example.com")
    db.commit()
    db.close()

    resp = client.post(
        "/feedback",
        json={"rating": 6},
        headers=_auth_header(4),
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "rating 須介於 1 至 5 之間"


def test_T5_submit_feedback_no_comment(client):
    """T5: 提交回饋成功（無留言），comment 為 NULL"""
    from app.db.connector import get_db

    db_gen = client.app.dependency_overrides[get_db]()
    db = next(db_gen)
    _seed_user(db, 5, "Eve", "eve@example.com")
    db.commit()
    db.close()

    resp = client.post(
        "/feedback",
        json={"rating": 3},
        headers=_auth_header(5),
    )
    assert resp.status_code == 201
    assert resp.json()["message"] == "回饋提交成功"

    # Verify comment is NULL in DB
    from app.db.connector import get_db as _get_db

    db2_gen = client.app.dependency_overrides[_get_db]()
    db2 = next(db2_gen)
    fb = db2.query(Feedback).filter(Feedback.user_id == 5).first()
    assert fb is not None
    assert fb.comment is None
    db2.close()


def test_T6_submit_feedback_unauthenticated(client):
    """T6: 提交回饋未登入"""
    resp = client.post("/feedback", json={"rating": 3})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /feedback
# ---------------------------------------------------------------------------


def _setup_admin_with_feedbacks(client, feedbacks: list[dict]) -> None:
    """Create admin user (id=10), regular user (id=11), and seed feedbacks."""
    from app.db.connector import get_db

    db_gen = client.app.dependency_overrides[get_db]()
    db = next(db_gen)

    _seed_user(db, 10, "Admin", "admin@example.com")
    _seed_user(db, 11, "Regular", "regular@example.com")

    _seed_role(db, 1, "Admin")
    _seed_role(db, 2, "User")

    _seed_user_role(db, 10, 1)  # admin -> Admin role
    _seed_user_role(db, 11, 2)  # regular -> User role

    _seed_fn_feedback_permission(db, 1)  # Admin role has fn_feedback permission

    for fb_data in feedbacks:
        db.add(
            Feedback(
                user_id=fb_data.get("user_id", 11),
                rating=fb_data["rating"],
                comment=fb_data.get("comment"),
            )
        )
    db.commit()
    db.close()


def test_T7_list_feedbacks_all(client):
    """T7: 查詢回饋列表成功（全部）"""
    _setup_admin_with_feedbacks(
        client,
        [
            {"user_id": 11, "rating": 3, "comment": "ok"},
            {"user_id": 11, "rating": 4, "comment": "good"},
            {"user_id": 11, "rating": 5, "comment": "great"},
        ],
    )
    resp = client.get("/feedback", headers=_auth_header(10))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert len(body["data"]) == 3
    # Each item must have user_name, rating, comment_summary, created_at
    for item in body["data"]:
        assert "user_name" in item
        assert "rating" in item
        assert "comment_summary" in item
        assert "created_at" in item


def test_T8_list_feedbacks_filtered_by_rating(client):
    """T8: 查詢回饋列表依 rating 篩選"""
    _setup_admin_with_feedbacks(
        client,
        [
            {"user_id": 11, "rating": 3},
            {"user_id": 11, "rating": 4},
            {"user_id": 11, "rating": 5},
        ],
    )
    resp = client.get("/feedback?rating=4", headers=_auth_header(10))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["rating"] == 4


def test_T9_list_feedbacks_empty(client):
    """T9: 查詢回饋列表無資料"""
    _setup_admin_with_feedbacks(client, [])
    resp = client.get("/feedback", headers=_auth_header(10))
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []


def test_T10_list_feedbacks_rating_out_of_range(client):
    """T10: 查詢回饋列表 rating 超出範圍"""
    _setup_admin_with_feedbacks(client, [])
    resp = client.get("/feedback?rating=6", headers=_auth_header(10))
    assert resp.status_code == 422
    assert resp.json()["detail"] == "rating 須介於 1 至 5 之間"


def test_T11_list_feedbacks_no_permission(client):
    """T11: 查詢回饋列表無權限（一般用戶）"""
    _setup_admin_with_feedbacks(client, [])
    resp = client.get("/feedback", headers=_auth_header(11))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "無此功能操作權限"


def test_T12_list_feedbacks_unauthenticated(client):
    """T12: 查詢回饋列表未登入"""
    resp = client.get("/feedback")
    assert resp.status_code == 401
