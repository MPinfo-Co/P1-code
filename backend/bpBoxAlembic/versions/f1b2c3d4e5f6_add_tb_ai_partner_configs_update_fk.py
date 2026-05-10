"""add tb_ai_partner_configs and update tb_ai_partner_tools fk

Revision ID: f1b2c3d4e5f6
Revises: a4f2c9d1e8b3
Create Date: 2026-05-10 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "a4f2c9d1e8b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tb_ai_partner_configs; drop role_definition/behavior_limit from tb_ai_partners;
    drop and recreate tb_ai_partner_tools with FK pointing to tb_ai_partner_configs."""

    # 1. Create tb_ai_partner_configs
    op.create_table(
        "tb_ai_partner_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("role_definition", sa.Text(), nullable=True),
        sa.Column("behavior_limit", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 2. Drop tb_ai_partner_tools (old FK → tb_ai_partners)
    op.drop_table("tb_ai_partner_tools")

    # 3. Recreate tb_ai_partner_tools with FK → tb_ai_partner_configs
    op.create_table(
        "tb_ai_partner_tools",
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["tb_ai_partner_configs.id"]),
        sa.ForeignKeyConstraint(["tool_id"], ["tb_tools.id"]),
        sa.PrimaryKeyConstraint("partner_id", "tool_id"),
    )

    # 4. Remove role_definition and behavior_limit from tb_ai_partners
    op.drop_column("tb_ai_partners", "role_definition")
    op.drop_column("tb_ai_partners", "behavior_limit")


def downgrade() -> None:
    """Reverse: restore role_definition/behavior_limit to tb_ai_partners;
    drop and recreate tb_ai_partner_tools with FK → tb_ai_partners;
    drop tb_ai_partner_configs."""

    # 1. Restore columns on tb_ai_partners
    op.add_column(
        "tb_ai_partners",
        sa.Column("role_definition", sa.Text(), nullable=True),
    )
    op.add_column(
        "tb_ai_partners",
        sa.Column("behavior_limit", sa.Text(), nullable=True),
    )

    # 2. Drop tb_ai_partner_tools (new FK → tb_ai_partner_configs)
    op.drop_table("tb_ai_partner_tools")

    # 3. Recreate tb_ai_partner_tools with FK → tb_ai_partners
    op.create_table(
        "tb_ai_partner_tools",
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["tb_ai_partners.id"]),
        sa.ForeignKeyConstraint(["tool_id"], ["tb_tools.id"]),
        sa.PrimaryKeyConstraint("partner_id", "tool_id"),
    )

    # 4. Drop tb_ai_partner_configs
    op.drop_table("tb_ai_partner_configs")
