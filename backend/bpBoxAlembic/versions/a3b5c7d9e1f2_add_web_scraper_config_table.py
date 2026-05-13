"""add_web_scraper_config_table

Revision ID: a3b5c7d9e1f2
Revises: 7b9034458136
Create Date: 2026-05-13 00:00:00.000000

Issue 318：新增 tb_tool_web_scraper_configs 表；調整 tb_tools 增加 tool_type 欄位
並允許 endpoint_url / http_method 為 NULL（支援 image_extract / web_scraper 類型）。
同時補建 tb_tool_image_fields 表（image_extract 類型使用）。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3b5c7d9e1f2"
down_revision: Union[str, Sequence[str], None] = "7b9034458136"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add tool_type column to tb_tools (default 'api_call' for existing rows)
    op.add_column(
        "tb_tools",
        sa.Column(
            "tool_type",
            sa.String(20),
            nullable=False,
            server_default="api_call",
        ),
    )

    # 2. Allow endpoint_url and http_method to be NULL
    op.alter_column("tb_tools", "endpoint_url", nullable=True)
    op.alter_column("tb_tools", "http_method", nullable=True)

    # 3. Create tb_tool_image_fields
    op.create_table(
        "tb_tool_image_fields",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tool_id",
            sa.Integer(),
            sa.ForeignKey("tb_tools.id"),
            nullable=False,
        ),
        sa.Column("field_name", sa.String(200), nullable=False),
        sa.Column("field_type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_index(
        "idx_tb_tool_image_fields_tool_id",
        "tb_tool_image_fields",
        ["tool_id"],
    )

    # 4. Create tb_tool_web_scraper_configs
    op.create_table(
        "tb_tool_web_scraper_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "tool_id",
            sa.Integer(),
            sa.ForeignKey("tb_tools.id"),
            nullable=False,
        ),
        sa.Column("target_url", sa.String(2000), nullable=False),
        sa.Column("extract_description", sa.Text(), nullable=False),
        sa.Column(
            "max_chars",
            sa.Integer(),
            nullable=False,
            server_default="4000",
        ),
    )
    op.create_index(
        "idx_tb_tool_web_scraper_configs_tool_id",
        "tb_tool_web_scraper_configs",
        ["tool_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_tb_tool_web_scraper_configs_tool_id",
        table_name="tb_tool_web_scraper_configs",
    )
    op.drop_table("tb_tool_web_scraper_configs")

    op.drop_index(
        "idx_tb_tool_image_fields_tool_id",
        table_name="tb_tool_image_fields",
    )
    op.drop_table("tb_tool_image_fields")

    op.alter_column("tb_tools", "http_method", nullable=False)
    op.alter_column("tb_tools", "endpoint_url", nullable=False)

    op.drop_column("tb_tools", "tool_type")
