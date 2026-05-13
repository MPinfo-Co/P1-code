"""seed mock users for tb_users

Revision ID: 7b9034458136
Revises: 3df16cb55fe2
Create Date: 2026-05-11 16:38:28.463730

Inserts 10 mock users for local/dev testing. All share password_hash =
sha256("tester"). Downgrade removes them by email so real accounts are
untouched.
"""

import hashlib
from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import column, table


revision: str = "7b9034458136"
down_revision: Union[str, Sequence[str], None] = "3df16cb55fe2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_PASSWORD_HASH = hashlib.sha256(b"tester").hexdigest()

_MOCK_USERS: list[dict[str, str]] = [
    {"name": "Avery Bennett", "email": "avery.bennett@example.com"},
    {"name": "Mira Caldwell", "email": "mira.caldwell@example.com"},
    {"name": "Theo Donovan", "email": "theo.donovan@example.com"},
    {"name": "Selene Park", "email": "selene.park@example.com"},
    {"name": "Rohan Iyer", "email": "rohan.iyer@example.com"},
    {"name": "Camille Hsu", "email": "camille.hsu@example.com"},
    {"name": "Jasper Quinn", "email": "jasper.quinn@example.com"},
    {"name": "Nadia Okoro", "email": "nadia.okoro@example.com"},
    {"name": "Felix Marchetti", "email": "felix.marchetti@example.com"},
    {"name": "Yuna Tanabe", "email": "yuna.tanabe@example.com"},
]


def upgrade() -> None:
    """Insert mock users. Earlier migrations seeded users with explicit ids
    without bumping ``tb_users_id_seq``; sync it before insert so nextval()
    does not collide with existing rows."""
    op.execute(
        "SELECT setval('tb_users_id_seq', COALESCE((SELECT MAX(id) FROM tb_users), 1))"
    )
    users = table(
        "tb_users",
        column("name"),
        column("email"),
        column("password_hash"),
    )
    op.bulk_insert(
        users,
        [
            {
                "name": u["name"],
                "email": u["email"],
                "password_hash": _PASSWORD_HASH,
            }
            for u in _MOCK_USERS
        ],
    )


def downgrade() -> None:
    """Remove only the mock users seeded by this migration."""
    emails = ", ".join(f"'{u['email']}'" for u in _MOCK_USERS)
    op.execute(f"DELETE FROM tb_users WHERE email IN ({emails})")
