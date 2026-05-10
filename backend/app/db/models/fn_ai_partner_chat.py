"""ORM models for fn_ai_partner_chat: tb_conversations, tb_messages, tb_role_ai_partners."""

from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Integer, JSON, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Conversation(Base):
    """對話會話紀錄，對應 tb_conversations。

    latest_suggestions 在 PostgreSQL 中以 TEXT[] 型別儲存；此 ORM 使用 JSON 型別
    以保持跨資料庫相容性（包含 SQLite 測試環境）。Migration 腳本使用 postgresql.ARRAY。
    """

    __tablename__ = "tb_conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=False
    )
    partner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_ai_partner_configs.id"), nullable=False
    )
    latest_suggestions: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )


class Message(Base):
    """對話訊息紀錄，對應 tb_messages。

    id 型別：ORM 使用 Integer 以相容 SQLite（測試環境）；
    migration 使用 BIGSERIAL（PostgreSQL），因此 DB 層實際為 BIGINT。
    """

    __tablename__ = "tb_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tb_conversations.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )


class RoleAiPartner(Base):
    """角色與 AI 夥伴的多對多關聯，對應 tb_role_ai_partners。"""

    __tablename__ = "tb_role_ai_partners"

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_roles.id"), primary_key=True
    )
    partner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_ai_partner_configs.id"), primary_key=True
    )
