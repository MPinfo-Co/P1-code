"""add fn_custom_table models and update tb_tools

Revision ID: b4c5d6e7f8a9
Revises: a3b5c7d9e1f2
Create Date: 2026-05-13 00:00:00.000000

sd-337: 新增 tb_custom_tables, tb_custom_table_fields, tb_custom_table_records。
        tb_tools 新增 custom_table_id（FK → tb_custom_tables）。
        tb_tool_image_fields 已廢棄，由 tb_custom_table_fields 取代（不刪除舊表以保留歷史資料）。
        新增 fn_custom_table 至 tb_function_items，並授權 admin role。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b4c5d6e7f8a9"
down_revision: Union[str, Sequence[str], None] = "a3b5c7d9e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 建立 tb_custom_tables
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

    # 2. 建立 tb_custom_table_fields
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
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["table_id"], ["tb_custom_tables.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tb_custom_table_fields_table_id",
        "tb_custom_table_fields",
        ["table_id"],
    )

    # 3. 建立 tb_custom_table_records
    op.create_table(
        "tb_custom_table_records",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.Column(
            "data",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("source_message_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["source_message_id"], ["tb_messages.id"]),
        sa.ForeignKeyConstraint(["table_id"], ["tb_custom_tables.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tb_custom_table_records_table_id",
        "tb_custom_table_records",
        ["table_id"],
    )

    # 4. tb_tools 新增 custom_table_id 欄位
    op.add_column(
        "tb_tools",
        sa.Column("custom_table_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_tb_tools_custom_table_id",
        "tb_tools",
        "tb_custom_tables",
        ["custom_table_id"],
        ["id"],
    )

    # 5. 將 fn_custom_table 功能項目寫入 tb_function_items（設定目錄 folder_id=2 設定目錄，sort_order=1）
    #    並授權 admin role（role_id=1）
    op.execute(
        """
        INSERT INTO tb_function_items (function_code, function_label, folder_id, sort_order)
        VALUES ('fn_custom_table', '自訂資料表', 2, 4)
        """
    )
    op.execute(
        """
        INSERT INTO tb_role_function (role_id, function_id)
        SELECT 1, function_id FROM tb_function_items WHERE function_code = 'fn_custom_table'
        """
    )


def downgrade() -> None:
    # 移除角色授權與功能項目
    op.execute(
        """
        DELETE FROM tb_role_function
        WHERE function_id = (
            SELECT function_id FROM tb_function_items WHERE function_code = 'fn_custom_table'
        )
        """
    )
    op.execute("DELETE FROM tb_function_items WHERE function_code = 'fn_custom_table'")

    # 移除 tb_tools.custom_table_id FK 與欄位
    op.drop_constraint("fk_tb_tools_custom_table_id", "tb_tools", type_="foreignkey")
    op.drop_column("tb_tools", "custom_table_id")

    # 刪除 tb_custom_table_records
    op.drop_index(
        "idx_tb_custom_table_records_table_id", table_name="tb_custom_table_records"
    )
    op.drop_table("tb_custom_table_records")

    # 刪除 tb_custom_table_fields
    op.drop_index(
        "idx_tb_custom_table_fields_table_id", table_name="tb_custom_table_fields"
    )
    op.drop_table("tb_custom_table_fields")

    # 刪除 tb_custom_tables
    op.drop_table("tb_custom_tables")
