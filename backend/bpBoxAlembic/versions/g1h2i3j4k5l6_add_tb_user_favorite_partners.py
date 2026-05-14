"""add tb_user_favorite_partners

Revision ID: g1h2i3j4k5l6
Revises: a3b5c7d9e1f2
Create Date: 2026-05-14 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, Sequence[str], None] = "a3b5c7d9e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tb_user_favorite_partners",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["tb_users.id"]),
        sa.ForeignKeyConstraint(["partner_id"], ["tb_ai_partner_configs.id"]),
        sa.PrimaryKeyConstraint("user_id", "partner_id"),
    )


def downgrade() -> None:
    op.drop_table("tb_user_favorite_partners")
