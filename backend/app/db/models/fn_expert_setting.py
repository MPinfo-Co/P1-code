"""ORM models for fn_expert_settings: tb_ai_partners, tb_expert_settings."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    TIMESTAMP,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class AiPartner(Base):
    """AI 夥伴主表。"""

    __tablename__ = "tb_ai_partners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
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
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ExpertSetting(Base):
    """資安專家設定表：儲存排程與 SSB 連線設定。"""

    __tablename__ = "tb_expert_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    partner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_ai_partners.id"), nullable=False, unique=True
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    frequency: Mapped[str] = mapped_column(
        String(10), nullable=False, default="daily", server_default="daily"
    )
    schedule_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    weekday: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    ssb_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ssb_port: Mapped[int] = mapped_column(
        Integer, nullable=False, default=443, server_default="443"
    )
    ssb_logspace: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ssb_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ssb_password_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )
