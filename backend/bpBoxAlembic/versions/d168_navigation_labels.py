"""rename folder/function columns and add label columns

Revision ID: d168_navigation_labels
Revises: c167_fn_auth_sidebar
Create Date: 2026-05-02 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d168_navigation_labels"
down_revision: Union[str, Sequence[str], None] = "c167_fn_auth_sidebar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- tb_function_folder ---
    op.alter_column("tb_function_folder", "name", new_column_name="folder_code")
    op.add_column(
        "tb_function_folder",
        sa.Column("folder_label", sa.String(50), nullable=True),
    )
    op.execute("UPDATE tb_function_folder SET folder_label = folder_code")
    op.execute("UPDATE tb_function_folder SET folder_code = 'ai_partner' WHERE id = 1")
    op.execute("UPDATE tb_function_folder SET folder_code = 'settings' WHERE id = 2")
    op.alter_column("tb_function_folder", "folder_label", nullable=False)

    # --- tb_functions ---
    op.alter_column("tb_functions", "function_name", new_column_name="function_code")
    op.add_column(
        "tb_functions",
        sa.Column("function_label", sa.String(50), nullable=True),
    )
    op.execute("UPDATE tb_functions SET function_label = 'AI 夥伴' WHERE function_code = 'fn_partner'")
    op.execute("UPDATE tb_functions SET function_label = '知識庫' WHERE function_code = 'fn_km'")
    op.execute("UPDATE tb_functions SET function_label = 'AI 夥伴管理' WHERE function_code = 'fn_ai_config'")
    op.execute("UPDATE tb_functions SET function_label = '使用者管理' WHERE function_code = 'fn_user'")
    op.execute("UPDATE tb_functions SET function_label = '角色管理' WHERE function_code = 'fn_role'")
    op.execute("UPDATE tb_functions SET function_label = function_code WHERE function_label IS NULL")
    op.alter_column("tb_functions", "function_label", nullable=False)


def downgrade() -> None:
    op.drop_column("tb_functions", "function_label")
    op.alter_column("tb_functions", "function_code", new_column_name="function_name")
    op.drop_column("tb_function_folder", "folder_label")
    op.execute("UPDATE tb_function_folder SET folder_code = 'AI 夥伴' WHERE id = 1")
    op.execute("UPDATE tb_function_folder SET folder_code = '設定' WHERE id = 2")
    op.alter_column("tb_function_folder", "folder_code", new_column_name="name")
