"""ORM models for fn_partner: tb_ai_partners, tb_role_ai_partners."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AiPartner(Base):
    """AI 夥伴定義。"""

    __tablename__ = "tb_ai_partners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    model_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class RoleAiPartner(Base):
    """角色與 AI 夥伴的多對多關聯。"""

    __tablename__ = "tb_role_ai_partners"

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_roles.id"), primary_key=True
    )
    partner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_ai_partners.id"), primary_key=True
    )
