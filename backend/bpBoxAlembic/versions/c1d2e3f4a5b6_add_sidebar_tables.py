"""add sidebar tables: tb_function_folder, tb_functions, tb_role_function

Revision ID: c1d2e3f4a5b6
Revises: 69f55dc2
Create Date: 2026-05-02 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "69f55dc2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """建立 tb_function_folder、tb_functions、tb_role_function，並 seed 初始資料。"""

    # 建立目錄資料表
    op.create_table(
        "tb_function_folder",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("default_open", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 建立功能代碼資料表
    op.create_table(
        "tb_functions",
        sa.Column("function_id", sa.Integer(), nullable=False),
        sa.Column("function_name", sa.String(100), nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["folder_id"], ["tb_function_folder.id"]),
        sa.PrimaryKeyConstraint("function_id"),
        sa.UniqueConstraint("function_name"),
    )

    # 建立角色-功能多對多關聯資料表
    op.create_table(
        "tb_role_function",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("function_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["tb_roles.id"]),
        sa.ForeignKeyConstraint(["function_id"], ["tb_functions.function_id"]),
        sa.PrimaryKeyConstraint("role_id", "function_id"),
    )

    # Seed: tb_function_folder 初始資料
    # (1, 'AI 夥伴', true, 1), (2, '設定', false, 2)
    op.execute(
        "INSERT INTO tb_function_folder (id, name, default_open, sort_order) VALUES "
        "(1, 'AI 夥伴', true, 1), "
        "(2, '設定', false, 2)"
    )
    op.execute(
        "SELECT setval('tb_function_folder_id_seq', (SELECT MAX(id) FROM tb_function_folder))"
    )

    # Seed: tb_functions 初始資料（folder_id 1 = AI 夥伴, folder_id 2 = 設定）
    op.execute(
        "INSERT INTO tb_functions (function_id, function_name, folder_id, sort_order) VALUES "
        "(1, 'fn_partner', 1, 1), "
        "(2, 'fn_km', 1, 2), "
        "(3, 'fn_ai_config', 1, 3), "
        "(4, 'fn_user', 2, 1), "
        "(5, 'fn_role', 2, 2), "
        "(6, 'fn_setting', 2, 3)"
    )
    op.execute(
        "SELECT setval('tb_functions_function_id_seq', (SELECT MAX(function_id) FROM tb_functions))"
    )

    # Seed: Admin role (role_id=1) 綁定全部 6 個功能
    op.execute(
        "INSERT INTO tb_role_function (role_id, function_id) VALUES "
        "(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6)"
    )


def downgrade() -> None:
    """移除 tb_role_function、tb_functions、tb_function_folder。"""
    op.drop_table("tb_role_function")
    op.drop_table("tb_functions")
    op.drop_table("tb_function_folder")
