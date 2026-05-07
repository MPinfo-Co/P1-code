"""ORM models for fn_expert Security Event: tb_security_events, tb_event_history."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SecurityEvent(Base):
    """Pro Task 彙整後的最終事件，為使用者清單頁的資料來源。"""

    __tablename__ = "tb_security_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    date_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    star_rank: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    affected_summary: Mapped[str] = mapped_column(String(100), nullable=False)
    affected_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    match_key: Mapped[str] = mapped_column(String(200), nullable=False)
    detection_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    continued_from: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tb_security_events.id"), nullable=True
    )
    assignee_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=True
    )
    suggests: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    logs: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    ioc_list: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    mitre_tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "star_rank BETWEEN 1 AND 5", name="ck_tb_security_events_star_rank"
        ),
        Index("idx_tb_security_events_event_date", "event_date"),
        Index("idx_tb_security_events_star_rank", star_rank.desc()),
        Index("idx_tb_security_events_current_status", "current_status"),
        Index("idx_tb_security_events_match_key", "match_key"),
    )


class EventHistory(Base):
    """安全事件的處理日誌，對應詳情頁「處理日誌」tab。"""

    __tablename__ = "tb_event_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tb_security_events.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("idx_tb_event_history_event_id", "event_id"),)
