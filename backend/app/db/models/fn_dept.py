"""ORM models for fn_dept: tb_departments."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Department(Base):
    """部門主表。"""

    __tablename__ = "tb_departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tb_departments.id"), nullable=True
    )
    manager_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tb_users.id", use_alter=True, name="fk_dept_manager"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
