"""add tb_skills and tb_skill_body_params

Revision ID: c3f1a8e20d99
Revises: 466b985000fb
Create Date: 2026-05-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3f1a8e20d99'
down_revision: Union[str, Sequence[str], None] = '466b985000fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: create tb_skills and tb_skill_body_params."""
    op.create_table(
        'tb_skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('endpoint_url', sa.String(length=2000), nullable=False),
        sa.Column('http_method', sa.String(length=10), nullable=False),
        sa.Column('auth_type', sa.String(length=20), nullable=False, server_default='none'),
        sa.Column('auth_header_name', sa.String(length=100), nullable=True),
        sa.Column('credential_enc', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    op.create_table(
        'tb_skill_body_params',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('param_name', sa.String(length=200), nullable=False),
        sa.Column('param_type', sa.String(length=20), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['skill_id'], ['tb_skills.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_tb_skill_body_params_skill_id', 'tb_skill_body_params', ['skill_id'])

    # Seed fn_skill function item and grant to admin role
    op.execute(
        "INSERT INTO tb_function_items (function_code, function_label, folder_id, sort_order) "
        "VALUES ('fn_skill', '技能管理', 2, 4)"
    )
    op.execute(
        "INSERT INTO tb_role_function (role_id, function_id) "
        "SELECT 1, function_id FROM tb_function_items WHERE function_code = 'fn_skill'"
    )


def downgrade() -> None:
    """Downgrade schema: remove tb_skills and tb_skill_body_params."""
    op.execute(
        "DELETE FROM tb_role_function WHERE function_id IN "
        "(SELECT function_id FROM tb_function_items WHERE function_code = 'fn_skill')"
    )
    op.execute("DELETE FROM tb_function_items WHERE function_code = 'fn_skill'")
    op.drop_index('idx_tb_skill_body_params_skill_id', table_name='tb_skill_body_params')
    op.drop_table('tb_skill_body_params')
    op.drop_table('tb_skills')
