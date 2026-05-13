"""merge two heads before nullable fix

Revision ID: a9b8c7d6e5f4
Revises: 67f626501ad0, 7b9034458136
Create Date: 2026-05-13 13:39:11.211443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9b8c7d6e5f4'
down_revision: Union[str, Sequence[str], None] = ('67f626501ad0', '7b9034458136')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
