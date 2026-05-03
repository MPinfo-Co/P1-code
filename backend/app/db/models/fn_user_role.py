"""ORM models for fn_user / role: tb_users, tb_roles, tb_user_roles, tb_token_blacklist."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

from .base import Base


class User(Base):
    """系統使用者帳號，所有人工操作的身份來源。"""

    __tablename__ = "tb_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tb_users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Role(Base):
    """角色定義。"""

    __tablename__ = "tb_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
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


class FunctionItem(Base):
    function_id: int
    function_name: str

    model_config = {"from_attributes": True}


class RoleUserItem(Base):
    id: int
    name: str

    model_config = {"from_attributes": True}


class RoleItem(Base):
    id: int
    name: str
    users: list[RoleUserItem] = []
    functions: list[FunctionItem] = []

    model_config = {"from_attributes": True}


class RoleCreate(Base):
    name: str
    user_ids: Optional[list[int]] = None
    function_ids: Optional[list[int]] = None


class RoleUpdate(Base):
    name: Optional[str] = None
    user_ids: Optional[list[int]] = None
    function_ids: Optional[list[int]] = None


class FunctionOptionItem(Base):
    function_id: int
    function_name: str

    model_config = {"from_attributes": True}