"""add tool_type to tb_tools and create tb_tool_image_fields, tb_tool_web_scraper_configs

Revision ID: a2b3c4d5e6f7
Revises: f3a1c8b92e05
Create Date: 2026-05-13 00:00:00.000000

新增 tb_tools.tool_type 欄位（DEFAULT 'external_api'），
調整 endpoint_url / http_method 為 NULLABLE，
建立 tb_tool_image_fields（image_extract 工具擷取欄位定義），
建立 tb_tool_web_scraper_configs（web_scraper 工具設定）。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "f3a1c8b92e05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add tool_type column to tb_tools
    op.add_column(
        "tb_tools",
        sa.Column(
            "tool_type",
            sa.String(20),
            nullable=False,
            server_default="external_api",
        ),
    )

    # 2. Make endpoint_url and http_method nullable
    op.alter_column(
        "tb_tools", "endpoint_url", existing_type=sa.String(2000), nullable=True
    )
    op.alter_column(
        "tb_tools", "http_method", existing_type=sa.String(10), nullable=True
    )

    # 3. Create tb_tool_image_fields
    op.create_table(
        "tb_tool_image_fields",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "tool_id",
            sa.Integer,
            sa.ForeignKey("tb_tools.id"),
            nullable=False,
        ),
        sa.Column("field_name", sa.String(200), nullable=False),
        sa.Column("field_type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index(
        "idx_tb_tool_image_fields_tool_id",
        "tb_tool_image_fields",
        ["tool_id"],
    )

    # 4. Create tb_tool_web_scraper_configs
    op.create_table(
        "tb_tool_web_scraper_configs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "tool_id",
            sa.Integer,
            sa.ForeignKey("tb_tools.id"),
            nullable=False,
        ),
        sa.Column("target_url", sa.String(2000), nullable=False),
        sa.Column("extract_description", sa.Text, nullable=False),
        sa.Column("max_chars", sa.Integer, nullable=False, server_default="4000"),
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

    op.alter_column(
        "tb_tools", "http_method", existing_type=sa.String(10), nullable=False
    )
    op.alter_column(
        "tb_tools", "endpoint_url", existing_type=sa.String(2000), nullable=False
    )

    op.drop_column("tb_tools", "tool_type")
