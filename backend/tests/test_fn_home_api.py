"""
Tests for fn_home APIs:
  GET   /home/partners
  POST  /home/favorite/toggle
"""

from sqlalchemy.orm import Session, sessionmaker

from app.db.models.fn_ai_partner_chat import RoleAiPartner
from app.db.models.fn_ai_partner_config import AiPartnerConfig
from app.db.models.fn_home import UserFavoritePartner
from app.db.models.function_access import FunctionFolder, FunctionItems, RoleFunction
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _make_folder(db: Session) -> int:
    f = FunctionFolder(folder_code="home_folder", folder_label="首頁", sort_order=0)
    db.add(f)
    db.flush()
    return f.id


def _make_role(db: Session, name: str) -> int:
    r = Role(name=name)
    db.add(r)
    db.flush()
    return r.id


def _make_user(db: Session, email: str, name: str = "Test") -> int:
    u = User(name=name, email=email, password_hash=hash_password("pw"))
    db.add(u)
    db.flush()
    return u.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _make_partner(db: Session, name: str, is_enabled: bool = True) -> int:
    p = AiPartnerConfig(
        name=name,
        description=f"描述: {name}",
        is_enabled=is_enabled,
    )
    db.add(p)
    db.flush()
    return p.id


def _bind_partner_to_role(db: Session, role_id: int, partner_id: int) -> None:
    db.add(RoleAiPartner(role_id=role_id, partner_id=partner_id))
    db.flush()


def _add_favorite(db: Session, user_id: int, partner_id: int) -> None:
    db.add(UserFavoritePartner(user_id=user_id, partner_id=partner_id))
    db.flush()


def _setup_user_with_role(engine, email: str = "home@test.com") -> tuple[int, int]:
    """Create user + role. Return (user_id, role_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, f"home_role_{email}")
    user_id = _make_user(db, email)
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id, role_id


# ---------------------------------------------------------------------------
# GET /home/partners
# ---------------------------------------------------------------------------


def test_list_home_partners_returns_is_favorite_true_and_false(client, engine):
    """對應 T1"""
    user_id, role_id = _setup_user_with_role(engine, "t1@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    p1 = _make_partner(db, "T1夥伴A")
    p2 = _make_partner(db, "T1夥伴B")
    _bind_partner_to_role(db, role_id, p1)
    _bind_partner_to_role(db, role_id, p2)
    _add_favorite(db, user_id, p1)
    db.commit()
    db.close()

    resp = client.get("/home/partners", headers=_auth(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    data = body["data"]
    assert len(data) == 2

    favorites = {item["id"]: item["is_favorite"] for item in data}
    assert favorites[p1] is True
    assert favorites[p2] is False


def test_list_home_partners_returns_empty_when_no_partners(client, engine):
    """對應 T2"""
    user_id, _ = _setup_user_with_role(engine, "t2@test.com")
    resp = client.get("/home/partners", headers=_auth(user_id))
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_list_home_partners_unauthenticated_returns_401(client, engine):
    """對應 T3"""
    resp = client.get("/home/partners")
    assert resp.status_code == 401


def test_list_home_partners_disabled_partner_not_included(client, engine):
    """已登入，角色有一個停用夥伴 → 不回傳該夥伴"""
    user_id, role_id = _setup_user_with_role(engine, "t_disabled@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    p1 = _make_partner(db, "停用夥伴", is_enabled=False)
    _bind_partner_to_role(db, role_id, p1)
    db.commit()
    db.close()

    resp = client.get("/home/partners", headers=_auth(user_id))
    assert resp.status_code == 200
    assert resp.json()["data"] == []


# ---------------------------------------------------------------------------
# POST /home/favorite/toggle
# ---------------------------------------------------------------------------


def test_toggle_favorite_add_returns_201(client, engine):
    """對應 T4：is_favorite=false → toggle → 201, is_favorite=true"""
    user_id, role_id = _setup_user_with_role(engine, "t4@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    p1 = _make_partner(db, "T4夥伴A")
    _bind_partner_to_role(db, role_id, p1)
    db.commit()
    db.close()

    resp = client.post(
        "/home/favorite/toggle",
        json={"partner_id": p1},
        headers=_auth(user_id),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["data"]["partner_id"] == p1
    assert body["data"]["is_favorite"] is True

    # 確認 DB 有新增一筆
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    row = (
        db.query(UserFavoritePartner)
        .filter(
            UserFavoritePartner.user_id == user_id,
            UserFavoritePartner.partner_id == p1,
        )
        .first()
    )
    db.close()
    assert row is not None


def test_toggle_favorite_remove_returns_200(client, engine):
    """對應 T5：is_favorite=true → toggle → 200, is_favorite=false"""
    user_id, role_id = _setup_user_with_role(engine, "t5@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    p1 = _make_partner(db, "T5夥伴A")
    _bind_partner_to_role(db, role_id, p1)
    _add_favorite(db, user_id, p1)
    db.commit()
    db.close()

    resp = client.post(
        "/home/favorite/toggle",
        json={"partner_id": p1},
        headers=_auth(user_id),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["partner_id"] == p1
    assert body["data"]["is_favorite"] is False

    # 確認 DB 已刪除
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    row = (
        db.query(UserFavoritePartner)
        .filter(
            UserFavoritePartner.user_id == user_id,
            UserFavoritePartner.partner_id == p1,
        )
        .first()
    )
    db.close()
    assert row is None


def test_toggle_favorite_unavailable_partner_returns_403(client, engine):
    """對應 T6：partner_id 不在使用者可用清單 → 403"""
    user_id, _ = _setup_user_with_role(engine, "t6@test.com")
    resp = client.post(
        "/home/favorite/toggle",
        json={"partner_id": 99},
        headers=_auth(user_id),
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_toggle_favorite_missing_partner_id_returns_422(client, engine):
    """對應 T7：partner_id 未填 → 422（Pydantic validation error）"""
    user_id, _ = _setup_user_with_role(engine, "t7@test.com")
    resp = client.post(
        "/home/favorite/toggle",
        json={},
        headers=_auth(user_id),
    )
    assert resp.status_code == 422


def test_toggle_favorite_unauthenticated_returns_401(client, engine):
    """對應 T8：未登入 → 401"""
    resp = client.post(
        "/home/favorite/toggle",
        json={"partner_id": 1},
    )
    assert resp.status_code == 401
