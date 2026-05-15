"""merge pg218 split_expert_setting_enabled with main heads

Revision ID: i1j2k3l4m5n6
Revises: c2d3e4f5a6b7, h2i3j4k5l6m7
Create Date: 2026-05-15 13:35:51.600894

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "i1j2k3l4m5n6"
down_revision: Union[str, Sequence[str], None] = ("c2d3e4f5a6b7", "h2i3j4k5l6m7")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
