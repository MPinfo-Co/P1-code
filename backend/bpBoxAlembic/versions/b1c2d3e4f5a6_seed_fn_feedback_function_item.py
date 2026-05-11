"""seed_fn_feedback_function_item

Revision ID: b1c2d3e4f5a6
Revises: a7b3c5d2e9f1
Create Date: 2026-05-11

fn_feedback 功能項目注冊至 tb_function_items，並授權給 Admin / User 角色。
"""

from typing import Sequence, Union

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a7b3c5d2e9f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO tb_function_items (function_id, function_code, function_label, folder_id, sort_order)
        VALUES (13, 'fn_feedback', '用戶回饋', 2, 3)
    """)
    op.execute("""
        INSERT INTO tb_role_function (role_id, function_id)
        VALUES (1, 13), (2, 13)
    """)


def downgrade() -> None:
    op.execute("DELETE FROM tb_role_function WHERE function_id = 13")
    op.execute("DELETE FROM tb_function_items WHERE function_id = 13")
