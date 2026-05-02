"""remove_is_active_from_tb_users

Revision ID: 69f55dc2
Revises: 31cf8ba73762
Create Date: 2026-05-02 02:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69f55dc2'
down_revision: Union[str, Sequence[str], None] = '31cf8ba73762'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove is_active column from tb_users."""
    op.drop_column('tb_users', 'is_active')


def downgrade() -> None:
    """Restore is_active column to tb_users."""
    op.add_column(
        'tb_users',
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true'),
        ),
    )
