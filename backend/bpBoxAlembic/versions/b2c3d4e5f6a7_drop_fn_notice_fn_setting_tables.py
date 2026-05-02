"""drop_fn_notice_fn_setting_tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove fn_notice and fn_setting tables and related role columns."""
    # Drop tb_notices (fn_notice)
    op.drop_table("tb_notices")
    # Drop tb_system_params (fn_setting)
    op.drop_table("tb_system_params")
    # Drop can_manage_notices column from tb_roles
    op.drop_column("tb_roles", "can_manage_notices")
    # Drop can_manage_settings column from tb_roles
    op.drop_column("tb_roles", "can_manage_settings")


def downgrade() -> None:
    """Downgrade is not supported for this migration."""
    pass
