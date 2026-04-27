from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class RoleOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class UserItem(BaseModel):
    name: str
    email: str
    is_active: bool
    roles: list[RoleOut] = []

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    message: str = "查詢成功"
    data: list[UserItem]


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role_ids: list[int]

    @field_validator("name")
    @classmethod
    def name_max_length(cls, v: str) -> str:
        if len(v) > 100:
            raise ValueError("使用者顯示名稱不可超過 100 字")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密碼最少 8 字元")
        return v

    @field_validator("role_ids")
    @classmethod
    def roles_not_empty(cls, v: list[int]) -> list[int]:
        if not v:
            raise ValueError("角色未設定")
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    role_ids: Optional[list[int]] = None

    @field_validator("name")
    @classmethod
    def name_max_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 100:
            raise ValueError("使用者顯示名稱不可超過 100 字")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 8:
            raise ValueError("密碼至少需要 8 個字元")
        return v

    @field_validator("role_ids")
    @classmethod
    def roles_not_empty(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        if v is not None and len(v) == 0:
            raise ValueError("角色不可為空")
        return v
