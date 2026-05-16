"""add_chart_data_column_to_tb_messages

Revision ID: j2k3l4m5n6o7
Revises: i1j2k3l4m5n6
Create Date: 2026-05-16 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "j2k3l4m5n6o7"
down_revision: Union[str, Sequence[str], None] = "i1j2k3l4m5n6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add chart_data JSONB column to tb_messages."""
    op.add_column(
        "tb_messages",
        sa.Column("chart_data", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    """Remove chart_data column from tb_messages."""
    op.drop_column("tb_messages", "chart_data")
