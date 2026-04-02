from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class LogBatch(Base):
    __tablename__ = "log_batches"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    time_from = Column(DateTime, nullable=False)
    time_to = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    records_fetched = Column(Integer, nullable=False, default=0)
    chunks_total = Column(Integer, nullable=False, default=0)
    chunks_done = Column(Integer, nullable=False, default=0)
    retry_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    flash_results = relationship(
        "FlashResult", back_populates="batch", cascade="all, delete-orphan"
    )


class FlashResult(Base):
    __tablename__ = "flash_results"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    batch_id = Column(
        BigInteger, ForeignKey("log_batches.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index = Column(Integer, nullable=False)
    chunk_size = Column(Integer, nullable=False)
    events = Column(JSONB, nullable=False, default=list)
    status = Column(String(20), nullable=False, default="pending")
    error_message = Column(Text)
    processed_at = Column(DateTime)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    batch = relationship("LogBatch", back_populates="flash_results")


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_date = Column(Date, nullable=False)
    date_end = Column(Date)
    star_rank = Column(SmallInteger, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    affected_summary = Column(String(20), nullable=False)
    affected_detail = Column(Text)
    current_status = Column(String(20), nullable=False, default="pending")
    match_key = Column(String(200), nullable=False)
    detection_count = Column(Integer, nullable=False, default=0)
    continued_from = Column(BigInteger, ForeignKey("security_events.id"))
    assignee_user_id = Column(Integer, ForeignKey("users.id"))
    suggests = Column(JSONB)
    logs = Column(JSONB)
    ioc_list = Column(JSONB)
    mitre_tags = Column(JSONB)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    history = relationship(
        "EventHistory", back_populates="event", cascade="all, delete-orphan"
    )


class DailyAnalysis(Base):
    __tablename__ = "daily_analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    analysis_date = Column(Date, nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="pending")
    flash_results_count = Column(Integer, nullable=False, default=0)
    events_created = Column(Integer, nullable=False, default=0)
    events_updated = Column(Integer, nullable=False, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )


class EventHistory(Base):
    __tablename__ = "event_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(
        BigInteger, ForeignKey("security_events.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(20), nullable=False)
    old_status = Column(String(20))
    new_status = Column(String(20))
    note = Column(Text)
    resolved_at = Column(DateTime)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    event = relationship("SecurityEvent", back_populates="history")
