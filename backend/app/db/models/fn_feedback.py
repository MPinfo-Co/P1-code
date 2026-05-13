"""ORM models for fn_feedback: tb_feedbacks."""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, SmallInteger, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Feedback(Base):
    """用戶回饋，對應 tb_feedbacks。"""

    __tablename__ = "tb_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=False
    )
    tenant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_tenants.id"), nullable=False, default=1, server_default="1"
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
