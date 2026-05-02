"""ORM models for fn_user / role: tb_users, tb_roles, tb_user_roles, tb_token_blacklist."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    """系統使用者帳號，所有人工操作的身份來源。"""

    __tablename__ = "tb_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    updated_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Role(Base):
    """角色定義與權限旗標。"""

    __tablename__ = "tb_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    can_access_ai: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    can_use_kb: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    can_manage_accounts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    can_manage_roles: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    can_edit_ai: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    can_manage_kb: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    can_manage_notices: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    can_manage_settings: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class UserRole(Base):
    """使用者與角色的多對多關聯。"""

    __tablename__ = "tb_user_roles"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_users.id"), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_roles.id"), primary_key=True
    )


class TokenBlacklist(Base):
    """已撤銷之 JWT 紀錄，依 token_jti 識別。"""

    __tablename__ = "tb_token_blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_jti: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expired_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
