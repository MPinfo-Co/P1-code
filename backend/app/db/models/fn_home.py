"""ORM models for fn_home: tb_user_favorite."""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserFavorite(Base):
    """使用者最愛設定（夥伴與資料表），對應 tb_user_favorite。"""

    __tablename__ = "tb_user_favorite"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_users.id"), primary_key=True
    )
    item_type: Mapped[str] = mapped_column(
        String(20), primary_key=True
    )  # 'partner' | 'table'
    item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
