"""add_tb_system_params_and_can_manage_settings

Revision ID: a1b2c3d4e5f6
Revises: 31cf8ba73762
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "31cf8ba73762"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 建立 tb_system_params
    op.create_table(
        "tb_system_params",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("param_type", sa.String(length=100), nullable=False),
        sa.Column("param_code", sa.String(length=200), nullable=False),
        sa.Column("param_value", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["updated_by"], ["tb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("param_code"),
    )
    # 新增 can_manage_settings 至 tb_roles
    op.add_column(
        "tb_roles",
        sa.Column(
            "can_manage_settings",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("tb_roles", "can_manage_settings")
    op.drop_table("tb_system_params")
