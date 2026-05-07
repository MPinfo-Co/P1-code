"""
Tests for GET /api/navigation API.
"""

from sqlalchemy.orm import sessionmaker

from app.db.models.function_access import (
    FunctionItems as Function,
    FunctionFolder,
    RoleFunction,
)
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password


def _setup_and_seed(engine) -> int:
    """Create navigation tables, seed data, return a valid user_id."""
    FunctionFolder.__table__.create(bind=engine, checkfirst=True)
    Function.__table__.create(bind=engine, checkfirst=True)
    RoleFunction.__table__.create(bind=engine, checkfirst=True)

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    db.add(
        FunctionFolder(
            id=1,
            folder_code="ai_partner",
            folder_label="AI 夥伴",
            default_open=True,
            sort_order=1,
        )
    )
    db.add(
        FunctionFolder(
            id=2,
            folder_code="settings",
            folder_label="設定",
            default_open=False,
            sort_order=2,
        )
    )
    db.flush()
    for fid, code, label, folder_id, sort in [
        (1, "fn_partner", "AI 夥伴", 1, 1),
        (2, "fn_ai_config", "AI 夥伴管理", 1, 2),
        (3, "fn_user", "使用者管理", 2, 1),
        (4, "fn_role", "角色管理", 2, 2),
    ]:
        db.add(
            Function(
                function_id=fid,
                function_code=code,
                function_label=label,
                folder_id=folder_id,
                sort_order=sort,
            )
        )
    role = Role(name="admin")
    db.add(role)
    db.flush()
    user = User(
        name="Test", email="nav@test.com", password_hash=hash_password("password123")
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    user_id = user.id
    db.close()
    return user_id


def test_get_navigation_returns_structure(client, engine):
    """對應 T8：已登入，GET /api/navigation 回傳完整目錄結構。"""
    user_id = _setup_and_seed(engine)
    token = create_access_token(user_id)
    resp = client.get("/api/navigation", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    folder_codes = [f["folder_code"] for f in data]
    assert "ai_partner" in folder_codes
    assert "settings" in folder_codes
    ai_folder = next(f for f in data if f["folder_code"] == "ai_partner")
    assert ai_folder["folder_label"] == "AI 夥伴"
    assert ai_folder["default_open"] is True
    item_codes = [i["function_code"] for i in ai_folder["items"]]
    assert "fn_partner" in item_codes
    assert "fn_ai_config" in item_codes


def test_get_navigation_unauthenticated_returns_401(client, engine):
    """對應 T9：未登入，GET /api/navigation 應回 401。"""
    resp = client.get("/api/navigation")
    assert resp.status_code == 401
