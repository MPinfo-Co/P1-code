"""pg-231: create tb_custom_tables, tb_custom_table_fields, tb_custom_table_records

Revision ID: f2a3b4c5d6e7
Revises: a3b5c7d9e1f2
Create Date: 2026-05-14 00:00:00.000000

此 migration 由 pg-231-fn-custom-table 分支建立。
pg-235-ai 分支加入此 stub 以維持遷移鏈完整性。
實際 DDL 已在 DB 中執行（合併於 pg-231 期間），此處為 no-op。
"""

from typing import Sequence, Union


revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "a3b5c7d9e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables created by pg-231 branch; already exist in DB. No-op.
    pass


def downgrade() -> None:
    # Tables managed by pg-231 branch; no-op for this stub.
    pass
