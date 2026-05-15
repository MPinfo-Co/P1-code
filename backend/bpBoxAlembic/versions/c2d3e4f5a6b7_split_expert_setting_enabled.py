"""split is_enabled to haiku/sonnet, add haiku_interval, drop frequency/weekday

Revision ID: c2d3e4f5a6b7
Revises: 7b9034458136
Create Date: 2026-05-14
"""

from alembic import op
import sqlalchemy as sa

revision = "c2d3e4f5a6b7"
down_revision = "7b9034458136"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tb_expert_settings",
        sa.Column(
            "haiku_enabled", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "tb_expert_settings",
        sa.Column(
            "haiku_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
    )
    op.add_column(
        "tb_expert_settings",
        sa.Column(
            "sonnet_enabled", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.execute(
        "UPDATE tb_expert_settings "
        "SET haiku_enabled = is_enabled, sonnet_enabled = is_enabled"
    )
    op.drop_column("tb_expert_settings", "is_enabled")
    op.drop_column("tb_expert_settings", "frequency")
    op.drop_column("tb_expert_settings", "weekday")


def downgrade() -> None:
    op.add_column(
        "tb_expert_settings",
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "tb_expert_settings",
        sa.Column(
            "frequency",
            sa.String(length=10),
            nullable=False,
            server_default="daily",
        ),
    )
    op.add_column(
        "tb_expert_settings",
        sa.Column("weekday", sa.SmallInteger(), nullable=True),
    )
    op.execute(
        "UPDATE tb_expert_settings SET is_enabled = (haiku_enabled OR sonnet_enabled)"
    )
    op.drop_column("tb_expert_settings", "sonnet_enabled")
    op.drop_column("tb_expert_settings", "haiku_interval_minutes")
    op.drop_column("tb_expert_settings", "haiku_enabled")
