"""add company data tables

Revision ID: a1c4e82fd901
Revises: b7ace231ff76
Create Date: 2026-05-05 08:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1c4e82fd901'
down_revision: Union[str, Sequence[str], None] = 'b7ace231ff76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add tb_ai_partners, tb_company_data, tb_partners_company_data."""
    op.create_table(
        'tb_ai_partners',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_builtin', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_enabled', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'tb_company_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'tb_partners_company_data',
        sa.Column('company_data_id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['company_data_id'], ['tb_company_data.id']),
        sa.ForeignKeyConstraint(['partner_id'], ['tb_ai_partners.id']),
        sa.PrimaryKeyConstraint('company_data_id', 'partner_id'),
    )


def downgrade() -> None:
    """Downgrade schema: drop tb_partners_company_data, tb_company_data, tb_ai_partners."""
    op.drop_table('tb_partners_company_data')
    op.drop_table('tb_company_data')
    op.drop_table('tb_ai_partners')
