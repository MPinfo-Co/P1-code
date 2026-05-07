"""rename fn_skill to fn_tool: tables, index, and function item

Revision ID: d9e2f4a61b88
Revises: c3f1a8e20d99
Create Date: 2026-05-06 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd9e2f4a61b88'
down_revision: Union[str, Sequence[str], None] = 'c3f1a8e20d99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename tb_skills→tb_tools, tb_skill_body_params→tb_tool_body_params, update function item."""
    # Drop old FK and index before renaming
    op.drop_index('idx_tb_skill_body_params_skill_id', table_name='tb_skill_body_params')
    op.drop_constraint('tb_skill_body_params_skill_id_fkey', 'tb_skill_body_params', type_='foreignkey')

    # Rename tables
    op.rename_table('tb_skills', 'tb_tools')
    op.rename_table('tb_skill_body_params', 'tb_tool_body_params')

    # Rename column skill_id → tool_id in tb_tool_body_params
    op.alter_column('tb_tool_body_params', 'skill_id', new_column_name='tool_id')

    # Recreate FK and index on new names
    op.create_foreign_key(
        'tb_tool_body_params_tool_id_fkey',
        'tb_tool_body_params', 'tb_tools',
        ['tool_id'], ['id'],
    )
    op.create_index('idx_tb_tool_body_params_tool_id', 'tb_tool_body_params', ['tool_id'])

    # Update tb_function_items: fn_skill → fn_tool, 技能管理 → AI工具管理, folder_id 2 → 1
    op.execute(
        "UPDATE tb_function_items "
        "SET function_code = 'fn_tool', function_label = 'AI工具管理', folder_id = 1 "
        "WHERE function_code = 'fn_skill'"
    )


def downgrade() -> None:
    """Reverse: restore fn_skill naming."""
    op.execute(
        "UPDATE tb_function_items "
        "SET function_code = 'fn_skill', function_label = '技能管理', folder_id = 2 "
        "WHERE function_code = 'fn_tool'"
    )

    op.drop_index('idx_tb_tool_body_params_tool_id', table_name='tb_tool_body_params')
    op.drop_constraint('tb_tool_body_params_tool_id_fkey', 'tb_tool_body_params', type_='foreignkey')

    op.alter_column('tb_tool_body_params', 'tool_id', new_column_name='skill_id')

    op.rename_table('tb_tool_body_params', 'tb_skill_body_params')
    op.rename_table('tb_tools', 'tb_skills')

    op.create_foreign_key(
        'tb_skill_body_params_skill_id_fkey',
        'tb_skill_body_params', 'tb_skills',
        ['skill_id'], ['id'],
    )
    op.create_index('idx_tb_skill_body_params_skill_id', 'tb_skill_body_params', ['skill_id'])
