"""move fn_custom_table to bottom of AI夥伴 folder

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-05-14 00:00:00.000000

將 fn_custom_table sort_order 由 3 改為 5，排在 AI 夥伴目錄最下方。
"""

from typing import Sequence, Union

from alembic import op

revision: str = "d6e7f8a9b0c1"
down_revision: Union[str, Sequence[str], None] = "c5d6e7f8a9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE tb_function_items SET sort_order = 5 WHERE function_code = 'fn_custom_table'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE tb_function_items SET sort_order = 3 WHERE function_code = 'fn_custom_table'"
    )
