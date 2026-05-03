from typing import Optional
from pydantic import BaseModel, EmailStr


class RoleItem(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class UserItem(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    roles: list[RoleItem] = []

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role_ids: list[int]


class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    role_ids: Optional[list[int]] = None


class RoleOptionItem(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class UserOptionItem(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
