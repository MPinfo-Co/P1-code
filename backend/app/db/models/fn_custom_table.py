"""ORM models for fn_custom_table: tb_custom_tables, tb_custom_table_fields, tb_custom_table_records.

Also includes tb_role_custom_tables (fn_custom_table_data_input)
and tb_custom_table_relations (fn_custom_table cross-table relations).
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Integer,
    String,
    Text,
    TIMESTAMP,
    UniqueConstraint,
)
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
    """AI 擷取結果寫入的自訂資料表資料列。

    TDD #1：移除 source_message_id、移除 user_id；
    updated_by 改為 NOT NULL，作為唯一使用者關聯欄位（用於 read_custom_table scope 過濾）。
    """

    __tablename__ = "tb_custom_table_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    table_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_custom_tables.id"), nullable=False, index=True
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    updated_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )


class RoleCustomTable(Base):
    """角色與自訂資料表的授權關聯，對應 tb_role_custom_tables。

    決定哪些角色的使用者可在資料輸入頁面操作哪些自訂資料表。
    """

    __tablename__ = "tb_role_custom_tables"

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_roles.id"), primary_key=True, index=True
    )
    table_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_custom_tables.id"), primary_key=True, index=True
    )


class CustomTableRelation(Base):
    """欄位層級跨表關聯表，對應 tb_custom_table_relations。

    儲存來源欄位 → 目標欄位的對應關係，供 AI 夥伴進行跨表分析。
    全系統共用（不綁定特定 AI 夥伴）。
    """

    __tablename__ = "tb_custom_table_relations"
    __table_args__ = (
        UniqueConstraint(
            "src_table_id",
            "src_field",
            "dst_table_id",
            "dst_field",
            name="uidx_tb_custom_table_relations",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    src_table_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tb_custom_tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    src_field: Mapped[str] = mapped_column(String(200), nullable=False)
    dst_table_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tb_custom_tables.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dst_field: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
