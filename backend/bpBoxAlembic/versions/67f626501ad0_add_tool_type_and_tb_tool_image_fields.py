"""add tool_type column to tb_tools and create tb_tool_image_fields table

Revision ID: 67f626501ad0
Revises: f3a1c8b92e05
Create Date: 2026-05-13 00:00:00.000000

新增 tb_tools.tool_type 欄位（VARCHAR(20), NOT NULL, DEFAULT 'external_api'）
以及 tb_tool_image_fields 表（image_extract 類型工具的欄位定義明細）。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "67f626501ad0"
down_revision: Union[str, Sequence[str], None] = "f3a1c8b92e05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tool_type column to tb_tools
    op.add_column(
        "tb_tools",
        sa.Column(
            "tool_type",
            sa.String(20),
            nullable=False,
            server_default="external_api",
        ),
    )

    # Create tb_tool_image_fields table
    op.create_table(
        "tb_tool_image_fields",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(200), nullable=False),
        sa.Column("field_type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.ForeignKeyConstraint(
            ["tool_id"],
            ["tb_tools.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tb_tool_image_fields_tool_id"),
        "tb_tool_image_fields",
        ["tool_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_tb_tool_image_fields_tool_id"),
        table_name="tb_tool_image_fields",
    )
    op.drop_table("tb_tool_image_fields")
    op.drop_column("tb_tools", "tool_type")
