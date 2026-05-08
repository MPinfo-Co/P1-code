"""remove fn_ai_config, swap fn_partner→fn_expert, reorder folders

Revision ID: c1e3f5a7b9d2
Revises: b8d2a1f3c7e9
Create Date: 2026-05-08 12:00:00.000000

Sidebar 重整第二輪:
- 移除 fn_ai_config (AI 夥伴管理整個拿掉)
- 移除 fn_partner, 新增 fn_expert (對話介面 / IssueList) 在「資安專家」folder
- 「資安專家」folder 移到最上 (sort_order 1), AI 夥伴=2, 設定=3
- 「資安專家」folder 內 sort_order 重排:
    fn_expert=1 (主功能在最上), fn_company_data=2, fn_expert_setting=3
"""

from typing import Sequence, Union

from alembic import op


revision: str = "c1e3f5a7b9d2"
down_revision: Union[str, Sequence[str], None] = "b8d2a1f3c7e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 移除 fn_ai_config 與 fn_partner 的 admin 授權與 function_item
    op.execute(
        "DELETE FROM tb_role_function "
        "WHERE function_id IN ("
        "SELECT function_id FROM tb_function_items WHERE function_code IN ('fn_ai_config', 'fn_partner')"
        ")"
    )
    op.execute(
        "DELETE FROM tb_function_items WHERE function_code IN ('fn_ai_config', 'fn_partner')"
    )

    # 2. folder sort_order: 資安專家 → 1, AI 夥伴 → 2, 設定 → 3
    op.execute("UPDATE tb_function_folder SET sort_order = 1 WHERE id = 3")
    op.execute("UPDATE tb_function_folder SET sort_order = 2 WHERE id = 1")
    op.execute("UPDATE tb_function_folder SET sort_order = 3 WHERE id = 2")

    # 3. 「資安專家」folder 內順序重排:
    #    fn_expert=1 (主功能最上), fn_company_data=2, fn_expert_setting=3
    op.execute(
        "UPDATE tb_function_items SET sort_order = 2 "
        "WHERE function_code = 'fn_company_data'"
    )
    op.execute(
        "UPDATE tb_function_items SET sort_order = 3 "
        "WHERE function_code = 'fn_expert_setting'"
    )

    # 4. 新增 fn_expert function_item (folder_id=3, sort_order=1 排最上) + admin 授權
    op.execute(
        "SELECT setval('tb_function_items_function_id_seq', "
        "COALESCE((SELECT MAX(function_id) FROM tb_function_items), 1))"
    )
    op.execute(
        "INSERT INTO tb_function_items (function_code, function_label, folder_id, sort_order) "
        "VALUES ('fn_expert', '資安專家', 3, 1)"
    )
    op.execute(
        "INSERT INTO tb_role_function (role_id, function_id) "
        "SELECT 1, function_id FROM tb_function_items WHERE function_code = 'fn_expert'"
    )


def downgrade() -> None:
    # 反向處理

    # 1. 移除 fn_expert
    op.execute(
        "DELETE FROM tb_role_function "
        "WHERE function_id IN ("
        "SELECT function_id FROM tb_function_items WHERE function_code = 'fn_expert'"
        ")"
    )
    op.execute("DELETE FROM tb_function_items WHERE function_code = 'fn_expert'")

    # 2. 還原資安專家 folder 內 sort_order (fn_company_data=1, fn_expert_setting=2)
    op.execute(
        "UPDATE tb_function_items SET sort_order = 1 "
        "WHERE function_code = 'fn_company_data'"
    )
    op.execute(
        "UPDATE tb_function_items SET sort_order = 2 "
        "WHERE function_code = 'fn_expert_setting'"
    )

    # 3. 還原 folder sort_order (AI 夥伴=1, 設定=2, 資安專家=3)
    op.execute("UPDATE tb_function_folder SET sort_order = 1 WHERE id = 1")
    op.execute("UPDATE tb_function_folder SET sort_order = 2 WHERE id = 2")
    op.execute("UPDATE tb_function_folder SET sort_order = 3 WHERE id = 3")

    # 4. 還原 fn_partner 與 fn_ai_config (用原本 466b985000fb 的 hard-coded id)
    op.execute(
        "INSERT INTO tb_function_items (function_id, function_code, function_label, folder_id, sort_order) VALUES "
        "(1, 'fn_partner', 'AI 夥伴', 1, 1), "
        "(3, 'fn_ai_config', 'AI 夥伴管理', 1, 3)"
    )
    op.execute(
        "INSERT INTO tb_role_function (role_id, function_id) "
        "SELECT 1, function_id FROM tb_function_items WHERE function_code IN ('fn_partner', 'fn_ai_config')"
    )
