"""add tb_tenants and tenant_id to all tables with RLS policies

Revision ID: a1b2c4d8e9f0
Revises: 3df16cb55fe2, b0c1d2e3f4a5
Create Date: 2026-05-13 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c4d8e9f0"
down_revision: Union[str, Sequence[str], None] = ("3df16cb55fe2", "b0c1d2e3f4a5")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 所有需要新增 tenant_id 的既有 table（共 23 張）
_TABLES_WITH_TENANT = [
    "tb_users",
    "tb_roles",
    "tb_feedbacks",
    "tb_function_folder",
    "tb_function_items",
    "tb_role_function",
    "tb_user_roles",
    "tb_token_blacklist",
    "tb_expert_settings",
    "tb_log_batches",
    "tb_chunk_results",
    "tb_daily_analysis",
    "tb_security_events",
    "tb_event_history",
    "tb_tools",
    "tb_tool_body_params",
    "tb_ai_partners",
    "tb_ai_partner_configs",
    "tb_ai_partner_tools",
    "tb_company_data",
    "tb_conversations",
    "tb_messages",
    "tb_role_ai_partners",
]


def upgrade() -> None:
    # ── Step 1: 建立 tb_tenants ──────────────────────────────────────────────
    op.create_table(
        "tb_tenants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # ── Step 2: 插入預設 tenant（id=1, name='default'）──────────────────────
    op.execute(
        "INSERT INTO tb_tenants (id, name) VALUES (1, 'default') ON CONFLICT DO NOTHING"
    )

    # ── Step 3: 為所有既有 table 新增 tenant_id（先允許 NULL）───────────────
    for table in _TABLES_WITH_TENANT:
        op.add_column(table, sa.Column("tenant_id", sa.Integer(), nullable=True))

    # ── Step 4: 回填所有 table 的 tenant_id = 1 ─────────────────────────────
    for table in _TABLES_WITH_TENANT:
        op.execute(f"UPDATE {table} SET tenant_id = 1 WHERE tenant_id IS NULL")

    # ── Step 5: 設定 NOT NULL 約束 ──────────────────────────────────────────
    for table in _TABLES_WITH_TENANT:
        op.alter_column(table, "tenant_id", existing_type=sa.Integer(), nullable=False)

    # ── Step 6: 新增 FK constraints ─────────────────────────────────────────
    for table in _TABLES_WITH_TENANT:
        op.create_foreign_key(
            f"fk_{table}_tenant_id",
            table,
            "tb_tenants",
            ["tenant_id"],
            ["id"],
        )

    # ── Step 7: 在 tb_users 插入預設 tenant 的 default_user（1_admin）───────
    op.execute(
        "INSERT INTO tb_users (name, email, password_hash, tenant_id) "
        "VALUES ('1_admin', '1_admin@tenant.local', "
        "encode(sha256('1_admin'::bytea), 'hex'), 1) "
        "ON CONFLICT (email) DO NOTHING"
    )

    # ── Step 8: 啟用 RLS 並建立 POLICY ──────────────────────────────────────
    for table in _TABLES_WITH_TENANT:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"USING (tenant_id = current_setting('app.current_tenant', TRUE)::INTEGER)"
        )
        # 允許 superuser / 管理腳本（如 migration）繞過 RLS
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    # ── Step 1: 移除 RLS POLICY 並停用 RLS ───────────────────────────────────
    for table in reversed(_TABLES_WITH_TENANT):
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # ── Step 2: 移除 FK constraints ──────────────────────────────────────────
    for table in reversed(_TABLES_WITH_TENANT):
        op.drop_constraint(f"fk_{table}_tenant_id", table, type_="foreignkey")

    # ── Step 3: 移除 tenant_id 欄位 ─────────────────────────────────────────
    for table in reversed(_TABLES_WITH_TENANT):
        op.drop_column(table, "tenant_id")

    # ── Step 4: 刪除 tb_tenants ──────────────────────────────────────────────
    op.drop_table("tb_tenants")
