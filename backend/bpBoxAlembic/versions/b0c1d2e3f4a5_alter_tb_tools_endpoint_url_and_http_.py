"""alter tb_tools endpoint_url and http_method to nullable

Revision ID: b0c1d2e3f4a5
Revises: a9b8c7d6e5f4
Create Date: 2026-05-13 13:39:15.470505

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0c1d2e3f4a5'
down_revision: Union[str, Sequence[str], None] = 'a9b8c7d6e5f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("tb_tools", "endpoint_url", existing_type=sa.String(2000), nullable=True)
    op.alter_column("tb_tools", "http_method", existing_type=sa.String(10), nullable=True)


def downgrade() -> None:
    op.execute("UPDATE tb_tools SET endpoint_url = '' WHERE endpoint_url IS NULL")
    op.execute("UPDATE tb_tools SET http_method = 'GET' WHERE http_method IS NULL")
    op.alter_column("tb_tools", "endpoint_url", existing_type=sa.String(2000), nullable=False)
    op.alter_column("tb_tools", "http_method", existing_type=sa.String(10), nullable=False)
