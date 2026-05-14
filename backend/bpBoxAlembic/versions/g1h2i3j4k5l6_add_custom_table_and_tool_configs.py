"""add fn_custom_table tables and write/read custom table tool configs

Revision ID: g1h2i3j4k5l6
Revises: a3b5c7d9e1f2
Create Date: 2026-05-14 00:00:00.000000

TDD #1: 調整 tb_custom_table_records：移除 source_message_id、移除 user_id；將 updated_by 改為 NOT NULL
TDD #2: 建立 tb_tool_write_custom_table_configs
TDD #3: 建立 tb_tool_read_custom_table_configs
（tb_custom_tables / tb_custom_table_fields 為 pg-231 分支新增，此 migration 一併加入）
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, Sequence[str], None] = "a3b5c7d9e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── tb_custom_tables ────────────────────────────────────────────────────
    op.create_table(
        "tb_custom_tables",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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

    # ── tb_custom_table_fields ───────────────────────────────────────────────
    op.create_table(
        "tb_custom_table_fields",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(200), nullable=False),
        sa.Column("field_type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.ForeignKeyConstraint(["table_id"], ["tb_custom_tables.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tb_custom_table_fields_table_id",
        "tb_custom_table_fields",
        ["table_id"],
    )

    # ── tb_custom_table_records ──────────────────────────────────────────────
    # TDD #1：updated_by NOT NULL；不含 source_message_id / user_id
    op.create_table(
        "tb_custom_table_records",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.Column(
            "data",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("updated_by", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["table_id"], ["tb_custom_tables.id"]),
        sa.ForeignKeyConstraint(["updated_by"], ["tb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tb_custom_table_records_table_id",
        "tb_custom_table_records",
        ["table_id"],
    )
    op.create_index(
        "idx_tb_custom_table_records_updated_by",
        "tb_custom_table_records",
        ["updated_by"],
    )

    # ── tb_tool_write_custom_table_configs ───────────────────────────────────
    op.create_table(
        "tb_tool_write_custom_table_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.Column("target_table_id", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["tool_id"], ["tb_tools.id"]),
        sa.ForeignKeyConstraint(["target_table_id"], ["tb_custom_tables.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tb_tool_write_custom_table_configs_tool_id",
        "tb_tool_write_custom_table_configs",
        ["tool_id"],
    )
    op.create_index(
        "idx_tb_tool_write_custom_table_configs_target_table_id",
        "tb_tool_write_custom_table_configs",
        ["target_table_id"],
    )

    # ── tb_tool_read_custom_table_configs ────────────────────────────────────
    op.create_table(
        "tb_tool_read_custom_table_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.Column("target_table_id", sa.Integer(), nullable=False),
        sa.Column(
            "limit",
            sa.Integer(),
            nullable=False,
            server_default="20",
        ),
        sa.Column(
            "scope",
            sa.String(10),
            nullable=False,
            server_default="self",
        ),
        sa.ForeignKeyConstraint(["tool_id"], ["tb_tools.id"]),
        sa.ForeignKeyConstraint(["target_table_id"], ["tb_custom_tables.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tb_tool_read_custom_table_configs_tool_id",
        "tb_tool_read_custom_table_configs",
        ["tool_id"],
    )
    op.create_index(
        "idx_tb_tool_read_custom_table_configs_target_table_id",
        "tb_tool_read_custom_table_configs",
        ["target_table_id"],
    )

    # ── 更新 tb_tools.tool_type default & check value ────────────────────────
    # tool_type 新增 write_custom_table / read_custom_table 合法值（欄位 VARCHAR，無 CHECK 約束）
    # 舊資料 default 值由 API 層控制，不需額外 DDL


def downgrade() -> None:
    op.drop_table("tb_tool_read_custom_table_configs")
    op.drop_table("tb_tool_write_custom_table_configs")
    op.drop_table("tb_custom_table_records")
    op.drop_table("tb_custom_table_fields")
    op.drop_table("tb_custom_tables")
