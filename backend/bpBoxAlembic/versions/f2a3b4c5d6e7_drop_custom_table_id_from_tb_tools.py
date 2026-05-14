"""drop custom_table_id from tb_tools

Revision ID: f2a3b4c5d6e7
Revises: e7f8a9b0c1d2
Create Date: 2026-05-14

image_extract 工具還原為使用 tb_tool_image_fields，移除 tb_tools 上的 custom_table_id 欄位。
"""

from alembic import op

revision = "f2a3b4c5d6e7"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("fk_tb_tools_custom_table_id", "tb_tools", type_="foreignkey")
    op.drop_column("tb_tools", "custom_table_id")


def downgrade() -> None:
    import sqlalchemy as sa

    op.add_column(
        "tb_tools",
        sa.Column("custom_table_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_tb_tools_custom_table_id",
        "tb_tools",
        "tb_custom_tables",
        ["custom_table_id"],
        ["id"],
        ondelete="SET NULL",
    )
