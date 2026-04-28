"""drop created_at from users

Revision ID: b1c3e2d4f5a6
Revises: 0a71f43523e4
Create Date: 2026-04-28 21:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'b1c3e2d4f5a6'
down_revision: Union[str, Sequence[str], None] = '0a71f43523e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in [c['name'] for c in inspect(bind).get_columns(table)]


def upgrade() -> None:
    if _column_exists('users', 'created_at'):
        op.drop_column('users', 'created_at')


def downgrade() -> None:
    if not _column_exists('users', 'created_at'):
        op.add_column('users', sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False))
