"""drop tb_ai_partners and reorganize sidebar with 資安專家 folder

Revision ID: b8d2a1f3c7e9
Revises: f3a1c8b92e05, c8e4f1d72a93
Create Date: 2026-05-08 00:00:00.000000

把 fn_company_data 與 fn_expert_setting 從 ai_partner 概念解綁:
- 拔掉 tb_ai_partners 與 tb_partners_company_data
- 建立 tb_expert_settings (單例設計, 無 partner_id)
- 新增「資安專家」sidebar folder (id=3)
- fn_company_data 從「AI 夥伴」folder 移到「資安專家」folder
- 新增 fn_expert_setting function_item, 授權 admin
- seed 單例 tb_expert_settings row (id=1)

兼任 merge migration: 同時合 f3a1c8b92e05 與 c8e4f1d72a93 兩條 main head。
取代原本 PG agent 寫的 a1b2c3d4e5f6 (那個 migration 從未被應用, 因為它試圖重建 main 已存在的 tb_ai_partners)。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8d2a1f3c7e9"
down_revision: Union[str, Sequence[str], None] = ("f3a1c8b92e05", "c8e4f1d72a93")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 移除 partner 多對多關聯表
    op.drop_table("tb_partners_company_data")

    # 2. 拔 tb_ai_partners
    op.drop_table("tb_ai_partners")

    # 3. 建立 tb_expert_settings (單例設計, 無 partner_id)
    op.create_table(
        "tb_expert_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("frequency", sa.String(10), nullable=False, server_default="daily"),
        sa.Column("schedule_time", sa.String(5), nullable=True),
        sa.Column("weekday", sa.SmallInteger(), nullable=True),
        sa.Column("ssb_host", sa.String(255), nullable=True),
        sa.Column("ssb_port", sa.Integer(), nullable=False, server_default="443"),
        sa.Column("ssb_logspace", sa.String(255), nullable=True),
        sa.Column("ssb_username", sa.String(255), nullable=True),
        sa.Column("ssb_password_enc", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. 新增「資安專家」folder (id=3)
    op.execute(
        "INSERT INTO tb_function_folder (id, folder_label, folder_code, default_open, sort_order) "
        "VALUES (3, '資安專家', 'expert', true, 3)"
    )

    # 5. fn_company_data 從 folder_id=1 移到 folder_id=3 (sort_order 1)
    op.execute(
        "UPDATE tb_function_items SET folder_id = 3, sort_order = 1 "
        "WHERE function_code = 'fn_company_data'"
    )

    # 6. 新增 fn_expert_setting function_item + admin 授權
    op.execute(
        "SELECT setval('tb_function_items_function_id_seq', "
        "COALESCE((SELECT MAX(function_id) FROM tb_function_items), 1))"
    )
    op.execute(
        "INSERT INTO tb_function_items (function_code, function_label, folder_id, sort_order) "
        "VALUES ('fn_expert_setting', '資安專家設定', 3, 2)"
    )
    op.execute(
        "INSERT INTO tb_role_function (role_id, function_id) "
        "SELECT 1, function_id FROM tb_function_items WHERE function_code = 'fn_expert_setting'"
    )

    # 7. tb_expert_settings 寫入單例 row (id=1)
    op.execute(
        "INSERT INTO tb_expert_settings (id, is_enabled, frequency, ssb_port) "
        "VALUES (1, false, 'daily', 443)"
    )
    op.execute(
        "SELECT setval('tb_expert_settings_id_seq', "
        "(SELECT MAX(id) FROM tb_expert_settings))"
    )


def downgrade() -> None:
    # 反向處理

    # 1. 移除 admin 授權與 fn_expert_setting function_item
    op.execute(
        "DELETE FROM tb_role_function "
        "WHERE function_id IN ("
        "SELECT function_id FROM tb_function_items WHERE function_code = 'fn_expert_setting'"
        ")"
    )
    op.execute(
        "DELETE FROM tb_function_items WHERE function_code = 'fn_expert_setting'"
    )

    # 2. fn_company_data 移回 folder_id=1, sort_order=2
    op.execute(
        "UPDATE tb_function_items SET folder_id = 1, sort_order = 2 "
        "WHERE function_code = 'fn_company_data'"
    )

    # 3. 移除「資安專家」folder
    op.execute("DELETE FROM tb_function_folder WHERE id = 3")

    # 4. 砍 tb_expert_settings
    op.drop_table("tb_expert_settings")

    # 5. 重建 tb_ai_partners
    op.create_table(
        "tb_ai_partners",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_builtin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # 6. 還原資安專家 partner seed
    op.execute(
        "INSERT INTO tb_ai_partners (id, name, description, is_builtin, is_enabled) "
        "VALUES (1, '資安專家', '排程、資料來源（syslog-ng Store Box）', true, true)"
    )
    op.execute(
        "SELECT setval('tb_ai_partners_id_seq', (SELECT MAX(id) FROM tb_ai_partners))"
    )

    # 7. 還原 tb_partners_company_data 表 + 4 筆 seed 連結
    op.create_table(
        "tb_partners_company_data",
        sa.Column("company_data_id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["company_data_id"], ["tb_company_data.id"]),
        sa.ForeignKeyConstraint(["partner_id"], ["tb_ai_partners.id"]),
        sa.PrimaryKeyConstraint("company_data_id", "partner_id"),
    )
    op.execute(
        "INSERT INTO tb_partners_company_data (company_data_id, partner_id) VALUES "
        "(1, 1), (2, 1), (3, 1), (4, 1)"
    )
