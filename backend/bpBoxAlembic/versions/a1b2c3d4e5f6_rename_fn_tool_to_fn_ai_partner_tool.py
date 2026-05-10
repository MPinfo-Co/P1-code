"""rename fn_tool to fn_ai_partner_tool in function_items

Revision ID: a1b2c3d4e5f6
Revises: f3a1c8b92e05
Create Date: 2026-05-10 00:00:00.000000

將 tb_function_items.function_code 從 fn_tool 改為 fn_ai_partner_tool，
對應 Epic #174 全面改名工作。
"""

from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "f3a1c8b92e05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE tb_function_items SET function_code = 'fn_ai_partner_tool' WHERE function_code = 'fn_tool'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE tb_function_items SET function_code = 'fn_tool' WHERE function_code = 'fn_ai_partner_tool'"
    )
