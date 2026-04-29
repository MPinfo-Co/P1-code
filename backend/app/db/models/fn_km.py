"""ORM models for fn_km (knowledge management): 8 tables covering KBs, documents, chunks, structured tables, and access maps."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class KnowledgeBase(Base):
    """知識庫定義。"""

    __tablename__ = "tb_knowledge_bases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class KbDocument(Base):
    """知識庫文件。"""

    __tablename__ = "tb_kb_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kb_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_knowledge_bases.id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    processing_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", server_default="pending"
    )
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    uploaded_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class KbDocChunk(Base):
    """文件切塊。embedding 在實際部署時改為 vector 型別。"""

    __tablename__ = "tb_kb_doc_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_kb_documents.id"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class KbTable(Base):
    """知識庫之結構化資料表。"""

    __tablename__ = "tb_kb_tables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kb_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_knowledge_bases.id"), nullable=False
    )
    table_name: Mapped[str] = mapped_column(String(200), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="custom", server_default="custom")
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class KbTableColumn(Base):
    """結構化資料表欄位定義。"""

    __tablename__ = "tb_kb_table_columns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_kb_tables.id"), nullable=False
    )
    column_name: Mapped[str] = mapped_column(String(200), nullable=False)
    column_type: Mapped[str] = mapped_column(String(50), nullable=False, default="text", server_default="text")
    column_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


class KbTableRow(Base):
    """結構化資料表的列資料。"""

    __tablename__ = "tb_kb_table_rows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    table_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_kb_tables.id"), nullable=False
    )
    row_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class RoleKbMap(Base):
    """角色可存取之知識庫關聯。"""

    __tablename__ = "tb_role_kb_map"

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_roles.id"), primary_key=True
    )
    kb_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_knowledge_bases.id"), primary_key=True
    )


class PartnerKbMap(Base):
    """AI 夥伴可使用之知識庫關聯。"""

    __tablename__ = "tb_partner_kb_map"

    partner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_ai_partners.id"), primary_key=True
    )
    kb_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_knowledge_bases.id"), primary_key=True
    )
