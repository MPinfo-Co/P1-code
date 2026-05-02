"""Pydantic schemas for /api/user endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MeResponse(BaseModel):
    """Response for GET /api/users/me."""

    message: str = "成功"
    data: "MeData"


class MeData(BaseModel):
    """Current user basic info plus accessible functions."""

    id: int
    name: str
    email: str
    functions: list[str]


MeResponse.model_rebuild()


class UserItem(BaseModel):
    """Single user row returned in the list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role_ids: list[int] = Field(default_factory=list)
    updated_at: datetime


class UserListOut(BaseModel):
    """Response for GET /api/user."""

    message: str = "查詢成功"
    data: list[UserItem]


class UserCreateRequest(BaseModel):
    """Body for `POST /api/user`."""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., description="User email; must be unique.")
    password: str = Field(..., description="Plain-text password; hashed before storage.")
    role_ids: list[int] = Field(default_factory=list, description="Role ids to grant to the user.")


class UserCreateOut(BaseModel):
    """Response for POST /api/user (201)."""

    message: str = "新增成功"


class UserUpdateRequest(BaseModel):
    """Body for `PATCH /api/user/{email}` — all fields optional."""

    name: str | None = Field(None, min_length=1, max_length=100)
    password: str | None = Field(None, description="New password; hashed before storage.")
    role_ids: list[int] | None = None


class UserUpdateOut(BaseModel):
    """Response for PATCH /api/user/{email} (200)."""

    message: str = "更新成功"


class UserDeleteOut(BaseModel):
    """Response for DELETE /api/user/{email} (200)."""

    message: str = "刪除成功"


class UserOptionItem(BaseModel):
    """Single item in the user options list."""

    id: int
    name: str


class UserOptionsOut(BaseModel):
    """Response for GET /api/user/options."""

    message: str = "查詢成功"
    data: list[UserOptionItem]


class RoleOptionItem(BaseModel):
    """Single item in the role options list."""

    id: int
    name: str


class RoleOptionsOut(BaseModel):
    """Response for GET /api/roles/options."""

    message: str = "查詢成功"
    data: list[RoleOptionItem]
