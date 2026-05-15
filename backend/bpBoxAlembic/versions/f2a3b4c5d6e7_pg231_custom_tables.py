"""pg-231: create tb_custom_tables, tb_custom_table_fields, tb_custom_table_records

Revision ID: f2a3b4c5d6e7
Revises: a3b5c7d9e1f2
Create Date: 2026-05-14 00:00:00.000000

原始 pg-231 分支以手動 DDL 建立此三張表，後來把 stub 進 migration 鏈時
upgrade() 留成 no-op。對 main 開發者本機因 DB 已有實體 table 而無感，
但全新 DB（含 CI、其他 merge main 進來的 PR 分支）會在後續 g1h2i3j4k5l6
嘗試 drop_constraint 時炸掉。本檔補上真正的 DDL，讓鏈條對任何乾淨 DB
都能 upgrade head。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "a3b5c7d9e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tb_custom_tables",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "tb_custom_table_fields",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(200), nullable=False),
        sa.Column("field_type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["table_id"], ["tb_custom_tables.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tb_custom_table_fields_table_id",
        "tb_custom_table_fields",
        ["table_id"],
    )

    # tb_custom_table_records: pg-231 原始版本
    #   - source_message_id 與其 FK 隨後在 g1h2i3j4k5l6 被 drop
    #   - updated_by 為 nullable，隨後 g1h2i3j4k5l6 alter 為 NOT NULL
    #   - table_id 索引在此建立；updated_by 索引由 g1h2i3j4k5l6 補上
    op.create_table(
        "tb_custom_table_records",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("source_message_id", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["table_id"], ["tb_custom_tables.id"]),
        sa.ForeignKeyConstraint(
            ["source_message_id"],
            ["tb_messages.id"],
            name="tb_custom_table_records_source_message_id_fkey",
        ),
        sa.ForeignKeyConstraint(["updated_by"], ["tb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_tb_custom_table_records_table_id",
        "tb_custom_table_records",
        ["table_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tb_custom_table_records_table_id",
        table_name="tb_custom_table_records",
    )
    op.drop_table("tb_custom_table_records")
    op.drop_index(
        "ix_tb_custom_table_fields_table_id",
        table_name="tb_custom_table_fields",
    )
    op.drop_table("tb_custom_table_fields")
    op.drop_table("tb_custom_tables")
