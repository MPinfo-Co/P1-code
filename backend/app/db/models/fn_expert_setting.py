"""ORM model for fn_expert_setting: tb_expert_settings (single-row settings)."""

from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class ExpertSetting(Base):
    """資安專家設定（單例）：兩個獨立排程（Haiku 抓 log / Sonnet 彙整）+ SSB 連線。

    系統僅保留一筆紀錄（id=1，由 migration seed 寫入）。
    """

    __tablename__ = "tb_expert_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Haiku 排程（自動抓 SSB log）
    haiku_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    haiku_interval_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30, server_default="30"
    )
    # Sonnet 排程（每日自動彙整）
    sonnet_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    schedule_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    # SSB 連線
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
