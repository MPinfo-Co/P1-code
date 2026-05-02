"""add_tb_functions_tb_role_function_update_tb_roles

Revision ID: c3d4e5f6a7b8
Revises: c167_fn_auth_sidebar
Create Date: 2026-05-02 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "c167_fn_auth_sidebar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove boolean permission columns from tb_roles (replaced by tb_role_function)."""
    for col in [
        "can_access_ai",
        "can_use_kb",
        "can_manage_accounts",
        "can_manage_roles",
        "can_edit_ai",
        "can_manage_kb",
    ]:
        op.drop_column("tb_roles", col)


def downgrade() -> None:
    """Restore boolean columns to tb_roles."""
    for col in [
        "can_access_ai",
        "can_use_kb",
        "can_manage_accounts",
        "can_manage_roles",
        "can_edit_ai",
        "can_manage_kb",
    ]:
        op.add_column(
            "tb_roles",
            sa.Column(col, sa.Boolean(), nullable=False, server_default="false"),
        )
