"""update fn_custom_table label and folder

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-05-14 00:00:00.000000

將 fn_custom_table 功能項目：
  - function_label 由「自訂資料表」改為「資料表管理」
  - 從「設定」目錄（folder_id=2）移至「AI 夥伴」目錄（folder_id=1）
  - sort_order 由 4 改為 3
"""

from typing import Sequence, Union

from alembic import op

revision: str = "c5d6e7f8a9b0"
down_revision: Union[str, Sequence[str], None] = "b4c5d6e7f8a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE tb_function_items
        SET function_label = '資料表管理', folder_id = 1, sort_order = 3
        WHERE function_code = 'fn_custom_table'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE tb_function_items
        SET function_label = '自訂資料表', folder_id = 2, sort_order = 4
        WHERE function_code = 'fn_custom_table'
        """
    )
