"""add_tb_functions_tb_role_function_update_tb_roles

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7, 69f55dc2
Create Date: 2026-05-02 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = ("b2c3d4e5f6a7", "69f55dc2")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tb_function_folder, tb_functions, tb_role_function; remove boolean columns from tb_roles; seed data."""

    # Drop remaining boolean columns from tb_roles (align with schema.md)
    for col in [
        "can_access_ai",
        "can_use_kb",
        "can_manage_accounts",
        "can_manage_roles",
        "can_edit_ai",
        "can_manage_kb",
    ]:
        op.drop_column("tb_roles", col)

    # Create tb_function_folder
    op.create_table(
        "tb_function_folder",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("default_open", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create tb_functions
    op.create_table(
        "tb_functions",
        sa.Column("function_id", sa.Integer(), nullable=False),
        sa.Column("function_name", sa.String(100), nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["folder_id"], ["tb_function_folder.id"]),
        sa.PrimaryKeyConstraint("function_id"),
        sa.UniqueConstraint("function_name"),
    )

    # Create tb_role_function
    op.create_table(
        "tb_role_function",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("function_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["function_id"], ["tb_functions.function_id"]),
        sa.ForeignKeyConstraint(["role_id"], ["tb_roles.id"]),
        sa.PrimaryKeyConstraint("role_id", "function_id"),
    )

    # Seed tb_function_folder
    op.execute(
        "INSERT INTO tb_function_folder (id, name, default_open, sort_order) VALUES "
        "(1, 'AI 夥伴', true, 1), "
        "(2, '設定', false, 2)"
    )
    op.execute("SELECT setval('tb_function_folder_id_seq', (SELECT MAX(id) FROM tb_function_folder))")

    # Seed tb_functions
    op.execute(
        "INSERT INTO tb_functions (function_id, function_name, folder_id, sort_order) VALUES "
        "(1, 'fn_partner', 1, 1), "
        "(2, 'fn_km', 1, 2), "
        "(3, 'fn_ai_config', 1, 3), "
        "(4, 'fn_user', 2, 1), "
        "(5, 'fn_role', 2, 2), "
        "(6, 'fn_setting', 2, 3)"
    )
    op.execute("SELECT setval('tb_functions_function_id_seq', (SELECT MAX(function_id) FROM tb_functions))")

    # Seed tb_role_function: Admin role (id=1) gets all 6 functions
    op.execute(
        "INSERT INTO tb_role_function (role_id, function_id) VALUES "
        "(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6)"
    )


def downgrade() -> None:
    """Remove tb_role_function, tb_functions, tb_function_folder; restore boolean columns."""
    op.drop_table("tb_role_function")
    op.drop_table("tb_functions")
    op.drop_table("tb_function_folder")

    # Restore boolean columns
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
