"""ORM models for fn_auth sidebar: tb_function_folder, tb_functions, tb_role_function."""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FunctionFolder(Base):
    """Sidebar 目錄，管理功能分組的名稱與展開狀態。"""

    __tablename__ = "tb_function_folder"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    default_open: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


class Function(Base):
    """系統功能清單，每筆對應一個 Sidebar 功能項目。"""

    __tablename__ = "tb_functions"

    function_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    function_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    folder_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_function_folder.id"), nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


class RoleFunction(Base):
    """角色與功能的多對多關聯。"""

    __tablename__ = "tb_role_function"

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_roles.id"), primary_key=True
    )
    function_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tb_functions.function_id"), primary_key=True
    )
