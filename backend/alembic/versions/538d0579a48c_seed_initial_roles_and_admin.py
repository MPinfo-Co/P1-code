"""seed initial roles and admin

Revision ID: 538d0579a48c
Revises: 4ccbef57de2b
Create Date: 2026-04-10 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.seed import seed_admin, seed_roles

# revision identifiers, used by Alembic.
revision: str = "538d0579a48c"
down_revision: Union[str, Sequence[str], None] = "4ccbef57de2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    seed_roles(conn)
    seed_admin(conn)


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
