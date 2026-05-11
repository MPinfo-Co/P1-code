"""add_tb_feedbacks

Revision ID: a7b3c5d2e9f1
Revises: f3a1c8b92e05
Create Date: 2026-05-11 00:00:00.000000

新增 tb_feedbacks 資料表，對應 fn_feedback 用戶回饋功能。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7b3c5d2e9f1"
down_revision: Union[str, Sequence[str], None] = "f3a1c8b92e05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tb_feedbacks",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["tb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("tb_feedbacks")
