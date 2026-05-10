"""seed fn_ai_partner_chat function item

Revision ID: b2d4f6a8c1e3
Revises: a9b3c5d7e1f2
Create Date: 2026-05-10 00:00:00.000000

新增 fn_ai_partner_chat 功能項目至 AI 夥伴 folder（folder_id=1, sort_order=1）。
同步授權 admin role (role_id=1)。
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2d4f6a8c1e3"
down_revision: Union[str, Sequence[str], None] = "a9b3c5d7e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "INSERT INTO tb_function_items (function_code, function_label, folder_id, sort_order) "
        "VALUES ('fn_ai_partner_chat', 'AI 夥伴對話', 1, 1)"
    )
    op.execute(
        "INSERT INTO tb_role_function (role_id, function_id) "
        "SELECT 1, function_id FROM tb_function_items WHERE function_code = 'fn_ai_partner_chat'"
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM tb_role_function WHERE function_id = "
        "(SELECT function_id FROM tb_function_items WHERE function_code = 'fn_ai_partner_chat')"
    )
    op.execute(
        "DELETE FROM tb_function_items WHERE function_code = 'fn_ai_partner_chat'"
    )
