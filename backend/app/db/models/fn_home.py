"""ORM models for fn_home: tb_user_favorite_partners."""

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

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
