"""Tests for fn_notice APIs: GET /api/notices, POST /api/notices."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.db.models.fn_notice import Notice
from app.db.models.fn_user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(db: Session, email: str, name: str = "Test User") -> int:
    user = User(name=name, email=email, password_hash=hash_password("pw"))
    db.add(user)
    db.flush()
    return user.id


def _make_role(db: Session, name: str, can_manage_notices: bool = False) -> int:
    role = Role(name=name, can_manage_notices=can_manage_notices)
    db.add(role)
    db.flush()
    return role.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _token(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _make_notice(db: Session, title: str, days_from_now: int = 1) -> None:
    db.add(
        Notice(
            title=title,
            content="內容",
            expires_at=date.today() + timedelta(days=days_from_now),
        )
    )
    db.flush()


# ---------------------------------------------------------------------------
# GET /api/notices
# ---------------------------------------------------------------------------


def test_list_notices_returns_valid_only(client, engine):
    """對應 T1"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "user@t1.com")
        _make_notice(db, "有效公告1", days_from_now=1)
        _make_notice(db, "有效公告2", days_from_now=2)
        db.add(
            Notice(
                title="逾期公告",
                content="content",
                expires_at=date.today() - timedelta(days=1),
            )
        )
        db.commit()

    resp = client.get("/api/notices", headers=_token(uid))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    titles = [n["title"] for n in body["data"]]
    assert "有效公告1" in titles
    assert "有效公告2" in titles
    assert "逾期公告" not in titles
    assert len(body["data"]) == 2


def test_list_notices_empty(client, engine):
    """對應 T2"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "user@t2.com")
        db.commit()

    resp = client.get("/api/notices", headers=_token(uid))
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_list_notices_unauthenticated(client):
    """對應 T3"""
    resp = client.get("/api/notices")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/notices
# ---------------------------------------------------------------------------


def test_create_notice_success(client, engine):
    """對應 T4"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "admin@t4.com")
        rid = _make_role(db, "管理員", can_manage_notices=True)
        _assign_role(db, uid, rid)
        db.commit()

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(
        "/api/notices",
        json={"title": "測試公告", "content": "內容文字", "expires_at": tomorrow},
        headers=_token(uid),
    )
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"


def test_create_notice_empty_title(client, engine):
    """對應 T5"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "admin@t5.com")
        rid = _make_role(db, "管理員T5", can_manage_notices=True)
        _assign_role(db, uid, rid)
        db.commit()

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(
        "/api/notices",
        json={"title": "", "content": "內容", "expires_at": tomorrow},
        headers=_token(uid),
    )
    assert resp.status_code == 400
    assert "標題" in resp.json()["detail"]


def test_create_notice_empty_content(client, engine):
    """對應 T6"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "admin@t6.com")
        rid = _make_role(db, "管理員T6", can_manage_notices=True)
        _assign_role(db, uid, rid)
        db.commit()

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(
        "/api/notices",
        json={"title": "標題", "content": "", "expires_at": tomorrow},
        headers=_token(uid),
    )
    assert resp.status_code == 400
    assert "內容" in resp.json()["detail"]


def test_create_notice_empty_expires_at(client, engine):
    """對應 T7"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "admin@t7.com")
        rid = _make_role(db, "管理員T7", can_manage_notices=True)
        _assign_role(db, uid, rid)
        db.commit()

    resp = client.post(
        "/api/notices",
        json={"title": "標題", "content": "內容", "expires_at": ""},
        headers=_token(uid),
    )
    assert resp.status_code == 400
    assert "有效期限" in resp.json()["detail"]


def test_create_notice_past_expires_at(client, engine):
    """對應 T8"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "admin@t8.com")
        rid = _make_role(db, "管理員T8", can_manage_notices=True)
        _assign_role(db, uid, rid)
        db.commit()

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    resp = client.post(
        "/api/notices",
        json={"title": "標題", "content": "內容", "expires_at": yesterday},
        headers=_token(uid),
    )
    assert resp.status_code == 400
    assert "有效期限" in resp.json()["detail"]


def test_create_notice_no_permission(client, engine):
    """對應 T9"""
    with engine.connect() as conn:
        db = Session(bind=conn)
        uid = _make_user(db, "user@t9.com")
        rid = _make_role(db, "一般角色T9", can_manage_notices=False)
        _assign_role(db, uid, rid)
        db.commit()

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(
        "/api/notices",
        json={"title": "標題", "content": "內容", "expires_at": tomorrow},
        headers=_token(uid),
    )
    assert resp.status_code == 403
