"""ORM model for fn_expert_setting: tb_expert_settings (single-row settings)."""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, SmallInteger, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class ExpertSetting(Base):
    """資安專家設定（單例）：儲存排程與 SSB 連線設定。

    系統僅保留一筆紀錄（id=1，由 migration seed 寫入）。
    """

    __tablename__ = "tb_expert_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_tenants.id"), nullable=False, default=1, server_default="1"
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
