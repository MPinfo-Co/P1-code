"""add tb_conversations, tb_messages, tb_role_ai_partners

Revision ID: a9b3c5d7e1f2
Revises: f1b2c3d4e5f6
Create Date: 2026-05-10 00:00:00.000000

新增三張資料表以支援 fn_ai_partner_chat 功能：
- tb_conversations：對話會話紀錄，含 latest_suggestions 欄位
- tb_messages：對話訊息紀錄
- tb_role_ai_partners：角色與 AI 夥伴多對多關聯
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a9b3c5d7e1f2"
down_revision: Union[str, Sequence[str], None] = "f1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # tb_conversations
    op.create_table(
        "tb_conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("tb_users.id"),
            nullable=False,
        ),
        sa.Column(
            "partner_id",
            sa.Integer,
            sa.ForeignKey("tb_ai_partner_configs.id"),
            nullable=False,
        ),
        sa.Column(
            "latest_suggestions",
            postgresql.JSONB(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "idx_tb_conversations_user_partner",
        "tb_conversations",
        ["user_id", "partner_id"],
    )

    # tb_messages
    op.create_table(
        "tb_messages",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "conversation_id",
            sa.String(36),
            sa.ForeignKey("tb_conversations.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "idx_tb_messages_conversation_id",
        "tb_messages",
        ["conversation_id"],
    )

    # tb_role_ai_partners
    op.create_table(
        "tb_role_ai_partners",
        sa.Column(
            "role_id",
            sa.Integer,
            sa.ForeignKey("tb_roles.id"),
            primary_key=True,
        ),
        sa.Column(
            "partner_id",
            sa.Integer,
            sa.ForeignKey("tb_ai_partner_configs.id"),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("tb_role_ai_partners")
    op.drop_index("idx_tb_messages_conversation_id", table_name="tb_messages")
    op.drop_table("tb_messages")
    op.drop_index("idx_tb_conversations_user_partner", table_name="tb_conversations")
    op.drop_table("tb_conversations")
