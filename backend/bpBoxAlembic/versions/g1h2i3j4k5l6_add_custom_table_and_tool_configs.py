"""add fn_custom_table tables and write/read custom table tool configs

Revision ID: g1h2i3j4k5l6
Revises: f2a3b4c5d6e7
Create Date: 2026-05-14 00:00:00.000000

TDD #1: 調整 tb_custom_table_records：移除 source_message_id；將 updated_by 改為 NOT NULL
TDD #2: 建立 tb_tool_write_custom_table_configs
TDD #3: 建立 tb_tool_read_custom_table_configs
（tb_custom_tables / tb_custom_table_fields 由 pg-231 分支建立，本分支接續使用）
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g1h2i3j4k5l6"
down_revision: Union[str, Sequence[str], None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── tb_custom_table_records 欄位調整（pg-231 已建立此表）──────────────────
    # 1. 先移除 source_message_id 的 FK，再刪除欄位
    op.drop_constraint(
        "tb_custom_table_records_source_message_id_fkey",
        "tb_custom_table_records",
        type_="foreignkey",
    )
    op.drop_column("tb_custom_table_records", "source_message_id")

    # 2. updated_by 改為 NOT NULL（FK 在 pg-231 已建立，略過）
    op.alter_column(
        "tb_custom_table_records",
        "updated_by",
        nullable=False,
    )

    # 3. 補 updated_by 索引（table_id 索引在 pg-231 已建立，略過）
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


def downgrade() -> None:
    op.drop_table("tb_tool_read_custom_table_configs")
    op.drop_table("tb_tool_write_custom_table_configs")
    op.drop_index(
        "idx_tb_custom_table_records_updated_by",
        table_name="tb_custom_table_records",
    )
    op.alter_column(
        "tb_custom_table_records",
        "updated_by",
        nullable=True,
    )
    op.add_column(
        "tb_custom_table_records",
        sa.Column("source_message_id", sa.BigInteger(), nullable=True),
    )
