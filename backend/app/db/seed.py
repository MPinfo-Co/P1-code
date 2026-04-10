"""初始資料 seed 函式，供 Alembic migration 與本機開發環境使用。"""

import bcrypt
import sqlalchemy as sa


_DEFAULT_ROLES = [
    {
        "name": "admin",
        "can_access_ai": True,
        "can_use_kb": True,
        "can_manage_accounts": True,
        "can_manage_roles": True,
        "can_edit_ai": True,
        "can_manage_kb": True,
    },
    {
        "name": "user",
        "can_access_ai": True,
        "can_use_kb": True,
        "can_manage_accounts": False,
        "can_manage_roles": False,
        "can_edit_ai": False,
        "can_manage_kb": False,
    },
]

_ADMIN_EMAIL = "admin@mpinfo.com.tw"
_ADMIN_NAME = "Admin"
_ADMIN_PASSWORD = "admin123"


def seed_roles(conn: sa.engine.Connection) -> None:
    """冪等插入預設角色。"""
    for role in _DEFAULT_ROLES:
        exists = conn.execute(
            sa.text("SELECT id FROM roles WHERE name = :name"),
            {"name": role["name"]},
        ).fetchone()
        if not exists:
            conn.execute(
                sa.text(
                    "INSERT INTO roles "
                    "(name, can_access_ai, can_use_kb, can_manage_accounts, "
                    "can_manage_roles, can_edit_ai, can_manage_kb) "
                    "VALUES (:name, :can_access_ai, :can_use_kb, :can_manage_accounts, "
                    ":can_manage_roles, :can_edit_ai, :can_manage_kb)"
                ),
                role,
            )


def seed_admin(conn: sa.engine.Connection) -> None:
    """冪等插入 admin 帳號並關聯 admin 角色。"""
    admin_user = conn.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": _ADMIN_EMAIL},
    ).fetchone()
    if admin_user:
        return

    password_hash = bcrypt.hashpw(_ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()

    result = conn.execute(
        sa.text(
            "INSERT INTO users (name, email, password_hash, is_active) "
            "VALUES (:name, :email, :password_hash, :is_active)"
        ),
        {
            "name": _ADMIN_NAME,
            "email": _ADMIN_EMAIL,
            "password_hash": password_hash,
            "is_active": True,
        },
    )
    user_id = result.lastrowid

    admin_role = conn.execute(
        sa.text("SELECT id FROM roles WHERE name = 'admin'"),
    ).fetchone()

    conn.execute(
        sa.text(
            "INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"
        ),
        {"user_id": user_id, "role_id": admin_role.id},
    )
