"""seed initial roles and admin

Revision ID: 538d0579a48c
Revises: 4ccbef57de2b
Create Date: 2026-04-10 00:00:00.000000

"""

from typing import Sequence, Union

import bcrypt
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "538d0579a48c"
down_revision: Union[str, Sequence[str], None] = "4ccbef57de2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

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


def upgrade() -> None:
    conn = op.get_bind()

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

    admin_user = conn.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": "admin@mpinfo.com.tw"},
    ).fetchone()
    if not admin_user:
        password_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        user_id = conn.execute(
            sa.text(
                "INSERT INTO users (name, email, password_hash, is_active) "
                "VALUES (:name, :email, :password_hash, :is_active) "
                "RETURNING id"
            ),
            {
                "name": "Admin",
                "email": "admin@mpinfo.com.tw",
                "password_hash": password_hash,
                "is_active": True,
            },
        ).scalar()
        admin_role = conn.execute(
            sa.text("SELECT id FROM roles WHERE name = 'admin'"),
        ).fetchone()
        conn.execute(
            sa.text(
                "INSERT INTO user_roles (user_id, role_id) VALUES (:user_id, :role_id)"
            ),
            {"user_id": user_id, "role_id": admin_role.id},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM user_roles WHERE user_id IN "
            "(SELECT id FROM users WHERE email = 'admin@mpinfo.com.tw')"
        )
    )
    conn.execute(sa.text("DELETE FROM users WHERE email = 'admin@mpinfo.com.tw'"))
    conn.execute(sa.text("DELETE FROM roles WHERE name IN ('admin', 'user')"))
