"""ORM models for fn_ai_partner_config: tb_ai_partners, tb_ai_partner_tools."""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class AiPartner(Base):
    """AI 夥伴主表，對應 tb_ai_partners。"""

    __tablename__ = "tb_ai_partners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_builtin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    role_definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    behavior_limit: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class AiPartnerTool(Base):
    """AI 夥伴與工具的多對多關聯，對應 tb_ai_partner_tools。"""

    __tablename__ = "tb_ai_partner_tools"

    partner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_ai_partners.id"), primary_key=True
    )
    tool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_tools.id"), primary_key=True
    )
