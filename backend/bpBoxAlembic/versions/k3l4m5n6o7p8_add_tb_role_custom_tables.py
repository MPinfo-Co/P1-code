"""add_tb_role_custom_tables

Revision ID: k3l4m5n6o7p8
Revises: j2k3l4m5n6o7
Create Date: 2026-05-16 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "k3l4m5n6o7p8"
down_revision: Union[str, Sequence[str], None] = "j2k3l4m5n6o7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tb_role_custom_tables for role-custom_table many-to-many authorization."""
    op.create_table(
        "tb_role_custom_tables",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("table_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["tb_roles.id"]),
        sa.ForeignKeyConstraint(["table_id"], ["tb_custom_tables.id"]),
        sa.PrimaryKeyConstraint("role_id", "table_id"),
    )
    op.create_index(
        "idx_tb_role_custom_tables_role_id",
        "tb_role_custom_tables",
        ["role_id"],
    )
    op.create_index(
        "idx_tb_role_custom_tables_table_id",
        "tb_role_custom_tables",
        ["table_id"],
    )


def downgrade() -> None:
    """Drop tb_role_custom_tables."""
    op.drop_index(
        "idx_tb_role_custom_tables_table_id", table_name="tb_role_custom_tables"
    )
    op.drop_index(
        "idx_tb_role_custom_tables_role_id", table_name="tb_role_custom_tables"
    )
    op.drop_table("tb_role_custom_tables")
