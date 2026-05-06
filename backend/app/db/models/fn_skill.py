"""ORM models for fn_skill: tb_skills, tb_skill_body_params."""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Skill(Base):
    """技能主表 — 外部 API 技能定義。"""

    __tablename__ = "tb_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    endpoint_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    http_method: Mapped[str] = mapped_column(String(10), nullable=False)
    auth_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="none", server_default="none"
    )
    auth_header_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    credential_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SkillBodyParam(Base):
    """技能 Body 參數定義明細表。"""

    __tablename__ = "tb_skill_body_params"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_skills.id"), nullable=False, index=True
    )
    param_name: Mapped[str] = mapped_column(String(200), nullable=False)
    param_type: Mapped[str] = mapped_column(String(20), nullable=False)
    is_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
