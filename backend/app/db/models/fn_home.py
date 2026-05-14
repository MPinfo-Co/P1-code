"""ORM models for fn_home: tb_user_favorite_partners."""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class UserFavoritePartner(Base):
    """使用者對 AI 夥伴的最愛設定，對應 tb_user_favorite_partners。"""

    __tablename__ = "tb_user_favorite_partners"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_users.id"), primary_key=True
    )
    partner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_ai_partner_configs.id"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, server_default=func.now()
    )
