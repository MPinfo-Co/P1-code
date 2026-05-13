"""add_web_scraper_config_table

Revision ID: a3b5c7d9e1f2
Revises: b0c1d2e3f4a5
Create Date: 2026-05-13 00:00:00.000000

Issue 318：新增 tb_tool_web_scraper_configs 表。
tool_type / nullable / tb_tool_image_fields 已由 image_extract Epic 的 migration 處理。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3b5c7d9e1f2"
down_revision: Union[str, Sequence[str], None] = "b0c1d2e3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
