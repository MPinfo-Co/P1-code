"""ORM models for fn_custom_table: tb_custom_tables, tb_custom_table_fields, tb_custom_table_records."""

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class CustomTable(Base):
    """自訂資料表定義。"""

    __tablename__ = "tb_custom_tables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class CustomTableField(Base):
    """自訂資料表欄位定義。"""

    __tablename__ = "tb_custom_table_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_custom_tables.id"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )


class CustomTableRecord(Base):
    """AI 擷取結果寫入的自訂資料表資料列。"""

    __tablename__ = "tb_custom_table_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    table_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_custom_tables.id"), nullable=False, index=True
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    source_message_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tb_messages.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
