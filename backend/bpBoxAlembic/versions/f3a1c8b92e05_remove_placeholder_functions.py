"""remove placeholder function items: fn_km and fn_setting

Revision ID: f3a1c8b92e05
Revises: d9e2f4a61b88
Create Date: 2026-05-07 00:00:00.000000

fn_km (知識庫) 和 fn_setting 是 466b985000fb migration 寫入的佔位資料，
尚無對應前端實作。fn_setting function item 與設定資料夾的 folder_code 撞名，
屬誤植。一併移除 admin role 對這兩筆的授權。
"""

from typing import Sequence, Union

from alembic import op

revision: str = "f3a1c8b92e05"
down_revision: Union[str, Sequence[str], None] = "d9e2f4a61b88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove admin grants for fn_km (id=2) and fn_setting (id=6)
    op.execute(
        "DELETE FROM tb_role_function "
        "WHERE function_id IN (SELECT function_id FROM tb_function_items WHERE function_code IN ('fn_km', 'fn_setting'))"
    )
    # Remove the function items themselves
    op.execute(
        "DELETE FROM tb_function_items WHERE function_code IN ('fn_km', 'fn_setting')"
    )


def downgrade() -> None:
    op.execute(
        "INSERT INTO tb_function_items (function_id, function_code, function_label, folder_id, sort_order) VALUES "
        "(2, 'fn_km', '知識庫', 1, 2), "
        "(6, 'fn_setting', '設定', 2, 3)"
    )
    op.execute(
        "INSERT INTO tb_role_function (role_id, function_id) VALUES (1, 2), (1, 6)"
    )
