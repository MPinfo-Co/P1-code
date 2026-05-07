"""add tb_ai_partners and tb_expert_settings tables

Revision ID: a1b2c3d4e5f6
Revises: f3a1c8b92e05
Create Date: 2026-05-07 00:00:00.000000

建立 fn_expert_settings 功能所需的 tb_ai_partners 與 tb_expert_settings 資料表。
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f3a1c8b92e05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tb_ai_partners
    op.create_table(
        'tb_ai_partners',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_builtin', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('model_name', sa.String(100), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # Create tb_expert_settings
    op.create_table(
        'tb_expert_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('frequency', sa.String(10), nullable=False, server_default='daily'),
        sa.Column('schedule_time', sa.String(5), nullable=True),
        sa.Column('weekday', sa.SmallInteger(), nullable=True),
        sa.Column('ssb_host', sa.String(255), nullable=True),
        sa.Column('ssb_port', sa.Integer(), nullable=False, server_default='443'),
        sa.Column('ssb_logspace', sa.String(255), nullable=True),
        sa.Column('ssb_username', sa.String(255), nullable=True),
        sa.Column('ssb_password_enc', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['partner_id'], ['tb_ai_partners.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('partner_id'),
    )

    # Seed 資安專家 AI partner
    op.execute(
        "INSERT INTO tb_ai_partners (name, is_builtin, is_enabled) "
        "VALUES ('資安專家', true, true)"
    )


def downgrade() -> None:
    op.drop_table('tb_expert_settings')
    op.drop_table('tb_ai_partners')
