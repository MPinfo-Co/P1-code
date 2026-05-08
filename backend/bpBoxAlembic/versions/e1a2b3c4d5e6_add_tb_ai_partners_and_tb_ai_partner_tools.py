"""add tb_ai_partners and tb_ai_partner_tools

Revision ID: e1a2b3c4d5e6
Revises: d9e2f4a61b88
Create Date: 2026-05-08 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "d9e2f4a61b88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tb_ai_partners (with role_definition / behavior_limit) and tb_ai_partner_tools."""
    op.create_table(
        "tb_ai_partners",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("role_definition", sa.Text(), nullable=True),
        sa.Column("behavior_limit", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "tb_ai_partner_tools",
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["partner_id"], ["tb_ai_partners.id"]),
        sa.ForeignKeyConstraint(["tool_id"], ["tb_tools.id"]),
        sa.PrimaryKeyConstraint("partner_id", "tool_id"),
    )


def downgrade() -> None:
    """Drop tb_ai_partner_tools and tb_ai_partners."""
    op.drop_table("tb_ai_partner_tools")
    op.drop_table("tb_ai_partners")
