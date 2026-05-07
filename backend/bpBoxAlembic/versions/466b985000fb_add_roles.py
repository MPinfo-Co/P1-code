"""Add roles

Revision ID: 466b985000fb
Revises: b7ace231ff76
Create Date: 2026-05-05 13:45:38.055883

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = "466b985000fb"
down_revision: Union[str, Sequence[str], None] = "a1c4e82fd901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create role with admin and user
    role_table = table(
        "tb_roles",
        column("id", sa.Integer),
        column("name", sa.String),
        column("created_at", sa.DateTime),
        column("updated_at", sa.DateTime),
    )
    op.bulk_insert(
        role_table,
        [
            {"id": 1, "name": "admin", "created_at": datetime.now()},
            {"id": 2, "name": "user", "created_at": datetime.now()},
        ],
    )

    # Assign admin to admin role
    user_role_table = table(
        "tb_user_roles", column("user_id", sa.Integer), column("role_id", sa.Integer)
    )
    op.bulk_insert(user_role_table, [{"user_id": 1, "role_id": 1}])

    # Sidebar function folder setup
    op.execute(
        "INSERT INTO tb_function_folder (id, folder_label, folder_code, default_open, sort_order) VALUES "
        "(1, 'AI 夥伴', 'fn_partner', true, 1), "
        "(2, '設定', 'fn_setting', false, 2)"
    )
    op.execute(
        "INSERT INTO tb_function_items (function_id, function_code, function_label,folder_id, sort_order) VALUES "
        "(1, 'fn_partner', 'AI 夥伴',1, 1), "
        "(2, 'fn_km', '知識庫', 1, 2), "
        "(3, 'fn_ai_config', 'AI 夥伴管理', 1, 3), "
        "(4, 'fn_user', '使用者管理', 2, 1), "
        "(5, 'fn_role', '角色管理', 2, 2), "
        "(6, 'fn_setting', '設定', 2, 3)"
    )

    # Give all function to admin
    op.execute(
        "INSERT INTO tb_role_function (role_id, function_id) VALUES "
        "(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "DELETE FROM tb_role_function "
        "WHERE role_id = 1 AND function_id IN (1, 2, 3, 4, 5, 6)"
    )
    op.execute("DELETE FROM tb_function_items WHERE function_id IN (1, 2, 3, 4, 5, 6)")
    op.execute("DELETE FROM tb_function_folder WHERE id IN (1, 2)")
    op.execute("DELETE FROM tb_user_roles WHERE user_id = 1 AND role_id = 1")
    op.execute("DELETE FROM tb_roles WHERE id IN (1, 2)")
