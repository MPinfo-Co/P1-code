"""ORM models for fn_ai_partner_tool: tb_tools, tb_tool_body_params, tb_tool_image_fields, tb_tool_web_scraper_configs."""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Tool(Base):
    """AI工具主表 — 外部 API / image_extract / web_scraper 工具定義。"""

    __tablename__ = "tb_tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_tenants.id"), nullable=False, default=1, server_default="1"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="api_call", server_default="api_call"
    )
    endpoint_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    http_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
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


class ToolBodyParam(Base):
    """AI工具 Body 參數定義明細表。"""

    __tablename__ = "tb_tool_body_params"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_tenants.id"), nullable=False, default=1, server_default="1"
    )
    tool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_tools.id"), nullable=False, index=True
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


class ToolImageField(Base):
    """AI工具圖片擷取欄位定義明細表（image_extract 類型使用）。"""

    __tablename__ = "tb_tool_image_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_tools.id"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )


class ToolWebScraperConfig(Base):
    """AI工具網頁擷取設定表（web_scraper 類型使用）。"""

    __tablename__ = "tb_tool_web_scraper_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_tools.id"), nullable=False, index=True
    )
    target_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    extract_description: Mapped[str] = mapped_column(Text, nullable=False)
    max_chars: Mapped[int] = mapped_column(
        Integer, nullable=False, default=4000, server_default="4000"
    )
