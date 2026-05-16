"""replace tb_user_favorite_partners with tb_user_favorite (unified type+id)

Revision ID: l4m5n6o7p8q9
Revises: k3l4m5n6o7p8
Create Date: 2026-05-16 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "l4m5n6o7p8q9"
down_revision: Union[str, Sequence[str], None] = "k3l4m5n6o7p8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tb_user_favorite",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.String(20), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["tb_users.id"]),
        sa.PrimaryKeyConstraint("user_id", "item_type", "item_id"),
    )
    op.execute(
        "INSERT INTO tb_user_favorite (user_id, item_type, item_id, sort_order) "
        "SELECT user_id, 'partner', partner_id, 0 FROM tb_user_favorite_partners"
    )
    op.drop_table("tb_user_favorite_partners")


def downgrade() -> None:
    op.create_table(
        "tb_user_favorite_partners",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["tb_users.id"]),
        sa.ForeignKeyConstraint(["partner_id"], ["tb_ai_partner_configs.id"]),
        sa.PrimaryKeyConstraint("user_id", "partner_id"),
    )
    op.execute(
        "INSERT INTO tb_user_favorite_partners (user_id, partner_id) "
        "SELECT user_id, item_id FROM tb_user_favorite WHERE item_type = 'partner'"
    )
    op.drop_table("tb_user_favorite")
