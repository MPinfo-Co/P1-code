"""ORM model for fn_company_data: tb_company_data."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CompanyData(Base):
    """公司背景資料，對應 tb_company_data。"""

    __tablename__ = "tb_company_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_tenants.id"), nullable=False, default=1, server_default="1"
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
