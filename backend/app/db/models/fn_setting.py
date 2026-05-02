"""ORM model for fn_setting: tb_system_params."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SystemParam(Base):
    """系統參數設定，管理員可修改參數值。"""

    __tablename__ = "tb_system_params"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    param_type: Mapped[str] = mapped_column(String(100), nullable=False)
    param_code: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    param_value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
