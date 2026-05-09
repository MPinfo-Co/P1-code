"""remove default_open from tb_function_folder

Revision ID: a4f2c9d1e8b3
Revises: b8d2a1f3c7e9
Create Date: 2026-05-09 00:00:00.000000

移除 tb_function_folder.default_open 欄位：
- 所有目錄初始狀態改為收合，由前端統一控制，不再依賴 DB 欄位決定展開狀態
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a4f2c9d1e8b3"
down_revision: Union[str, Sequence[str], None] = "e1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("tb_function_folder", "default_open")


def downgrade() -> None:
    op.add_column(
        "tb_function_folder",
        sa.Column(
            "default_open",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
