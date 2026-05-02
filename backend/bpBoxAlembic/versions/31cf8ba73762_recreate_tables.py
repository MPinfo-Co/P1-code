"""recreate tables

Revision ID: 31cf8ba73762
Revises:
Create Date: 2026-04-29 16:47:33.836092

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '31cf8ba73762'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop old unprefixed tables and create tb_* schema."""
    # Drop old tables (CASCADE handles FK dependencies)
    for tbl in [
        "role_functions", "user_roles", "token_blacklist",
        "security_events", "event_history", "log_batches",
        "daily_analysis", "roles", "users",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE")

    op.create_table(
        "tb_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["updated_by"], ["tb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "tb_roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("can_access_ai", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("can_use_kb", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("can_manage_accounts", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("can_manage_roles", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("can_edit_ai", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("can_manage_kb", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("can_manage_notices", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "tb_user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["tb_users.id"]),
        sa.ForeignKeyConstraint(["role_id"], ["tb_roles.id"]),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    op.create_table(
        "tb_token_blacklist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_jti", sa.String(255), nullable=False),
        sa.Column("expired_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["updated_by"], ["tb_users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_jti"),
    )

    # Seed default user (SHA-256 hash: admin=admin123)
    op.execute(
        "INSERT INTO tb_users (id, name, email, password_hash, is_active) VALUES "
        "(1, 'Admin', 'admin@mpinfo.com.tw', "
        "'240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', true)"
    )
    op.execute("SELECT setval('tb_users_id_seq', (SELECT MAX(id) FROM tb_users))")

    # Seed default roles
    op.execute(
        "INSERT INTO tb_roles (id, name, can_access_ai, can_use_kb, can_manage_accounts, "
        "can_manage_roles, can_edit_ai, can_manage_kb, can_manage_notices) VALUES "
        "(1, 'Admin',  true, true, true, true, true, true, true), "
        "(2, 'User',   true, true, false, false, false, false, false), "
        "(3, 'Viewer', false, false, false, false, false, false, false)"
    )
    op.execute("SELECT setval('tb_roles_id_seq', (SELECT MAX(id) FROM tb_roles))")

    # Bind Admin user to Admin role
    op.execute("INSERT INTO tb_user_roles (user_id, role_id) VALUES (1, 1)")


def downgrade() -> None:
    """Drop tb_* tables created in this migration."""
    op.drop_table("tb_token_blacklist")
    op.drop_table("tb_user_roles")
    op.drop_table("tb_roles")
    op.drop_table("tb_users")
