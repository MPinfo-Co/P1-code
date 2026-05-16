"""add tb_custom_table_relations

Revision ID: m5n6o7p8q9r0
Revises: l4m5n6o7p8q9
Create Date: 2026-05-16 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "m5n6o7p8q9r0"
down_revision: Union[str, Sequence[str], None] = "l4m5n6o7p8q9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tb_custom_table_relations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("src_table_id", sa.Integer(), nullable=False),
        sa.Column("src_field", sa.String(200), nullable=False),
        sa.Column("dst_table_id", sa.Integer(), nullable=False),
        sa.Column("dst_field", sa.String(200), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["src_table_id"], ["tb_custom_tables.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["dst_table_id"], ["tb_custom_tables.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "src_table_id",
            "src_field",
            "dst_table_id",
            "dst_field",
            name="uidx_tb_custom_table_relations",
        ),
    )
    op.create_index(
        "idx_tb_custom_table_relations_src_table_id",
        "tb_custom_table_relations",
        ["src_table_id"],
    )
    op.create_index(
        "idx_tb_custom_table_relations_dst_table_id",
        "tb_custom_table_relations",
        ["dst_table_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_tb_custom_table_relations_dst_table_id",
        table_name="tb_custom_table_relations",
    )
    op.drop_index(
        "idx_tb_custom_table_relations_src_table_id",
        table_name="tb_custom_table_relations",
    )
    op.drop_table("tb_custom_table_relations")
