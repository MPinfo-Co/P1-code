"""merge ai_partner_tool + fn_feedback heads

Revision ID: 3df16cb55fe2
Revises: a1b2c3d4e5f6, b1c2d3e4f5a6
Create Date: 2026-05-11 16:37:46.653212

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "3df16cb55fe2"
down_revision: Union[str, Sequence[str], None] = ("a1b2c3d4e5f6", "b1c2d3e4f5a6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
