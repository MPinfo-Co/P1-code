"""add updated_by to users

Revision ID: 0a71f43523e4
Revises: 538d0579a48c
Create Date: 2026-04-28 21:35:20.376430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '0a71f43523e4'
down_revision: Union[str, Sequence[str], None] = '538d0579a48c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in [c['name'] for c in inspect(bind).get_columns(table)]


def upgrade() -> None:
    if not _column_exists('users', 'updated_by'):
        op.add_column('users', sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))


def downgrade() -> None:
    if _column_exists('users', 'updated_by'):
        op.drop_column('users', 'updated_by')
