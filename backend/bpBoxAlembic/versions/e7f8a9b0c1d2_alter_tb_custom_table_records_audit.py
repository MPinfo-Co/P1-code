"""Alter tb_custom_table_records: replace created_at with updated_by + updated_at.

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-05-14
"""

from alembic import op
import sqlalchemy as sa

revision = "e7f8a9b0c1d2"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("tb_custom_table_records", "created_at")
    op.add_column(
        "tb_custom_table_records",
        sa.Column(
            "updated_by",
            sa.Integer(),
            sa.ForeignKey("tb_users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "tb_custom_table_records",
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_column("tb_custom_table_records", "updated_at")
    op.drop_column("tb_custom_table_records", "updated_by")
    op.add_column(
        "tb_custom_table_records",
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
