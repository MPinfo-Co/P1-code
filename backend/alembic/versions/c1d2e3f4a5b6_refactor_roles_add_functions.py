"""refactor roles: remove can_* columns, add functions and role_functions tables

Revision ID: c1d2e3f4a5b6
Revises: 538d0579a48c
Create Date: 2026-04-29 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b1c3e2d4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Remove can_* columns from roles
    op.drop_column("roles", "can_access_ai")
    op.drop_column("roles", "can_use_kb")
    op.drop_column("roles", "can_manage_accounts")
    op.drop_column("roles", "can_manage_roles")
    op.drop_column("roles", "can_edit_ai")
    op.drop_column("roles", "can_manage_kb")

    # 2. Create tb_functions table
    op.create_table(
        "functions",
        sa.Column("function_id", sa.Integer(), nullable=False),
        sa.Column("function_name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("function_id"),
        sa.UniqueConstraint("function_name"),
    )

    # 3. Create tb_role_function table
    op.create_table(
        "role_functions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("function_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["function_id"], ["functions.function_id"]),
        sa.PrimaryKeyConstraint("role_id", "function_id"),
    )

    # 4. Seed initial functions data
    conn = op.get_bind()
    for fn_id, fn_name in [(1, "fn_user"), (2, "fn_role")]:
        exists = conn.execute(
            sa.text("SELECT function_id FROM functions WHERE function_id = :fid"),
            {"fid": fn_id},
        ).fetchone()
        if not exists:
            conn.execute(
                sa.text(
                    "INSERT INTO functions (function_id, function_name) "
                    "VALUES (:fid, :fname)"
                ),
                {"fid": fn_id, "fname": fn_name},
            )


def downgrade() -> None:
    op.drop_table("role_functions")
    op.drop_table("functions")

    op.add_column(
        "roles", sa.Column("can_access_ai", sa.Boolean(), nullable=False, server_default="false")
    )
    op.add_column(
        "roles", sa.Column("can_use_kb", sa.Boolean(), nullable=False, server_default="false")
    )
    op.add_column(
        "roles", sa.Column("can_manage_accounts", sa.Boolean(), nullable=False, server_default="false")
    )
    op.add_column(
        "roles", sa.Column("can_manage_roles", sa.Boolean(), nullable=False, server_default="false")
    )
    op.add_column(
        "roles", sa.Column("can_edit_ai", sa.Boolean(), nullable=False, server_default="false")
    )
    op.add_column(
        "roles", sa.Column("can_manage_kb", sa.Boolean(), nullable=False, server_default="false")
    )
