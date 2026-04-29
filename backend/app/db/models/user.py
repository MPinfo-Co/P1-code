from sqlalchemy import Boolean, Column, Integer, String, TIMESTAMP, ForeignKey, func
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)


class Function(Base):
    __tablename__ = "functions"

    function_id = Column(Integer, primary_key=True)
    function_name = Column(String(100), nullable=False, unique=True)


class RoleFunction(Base):
    __tablename__ = "role_functions"

    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    function_id = Column(Integer, ForeignKey("functions.function_id"), primary_key=True)
