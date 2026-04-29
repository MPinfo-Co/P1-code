"""Pydantic schemas for /user endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSummary(BaseModel):
    """Compact user row used for the user list view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    is_active: bool
    role_ids: list[int] = Field(default_factory=list)
    updated_at: datetime


class UserListResponse(BaseModel):
    """List of users."""

    items: list[UserSummary]
    total: int


class UserCreateRequest(BaseModel):
    """Body for `POST /user`."""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., description="User email; must be unique.")
    password: str = Field(..., min_length=1, description="Plain-text password; hashed before storage.")
    role_ids: list[int] = Field(default_factory=list, description="Role ids to grant to the user.")


class UserCreateResponse(BaseModel):
    """Result of creating a user."""

    id: int
    name: str
    email: EmailStr


class UserUpdateRequest(BaseModel):
    """Body for `PATCH /user/{user_id}` — all fields optional."""

    name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(None, min_length=1)
    role_ids: list[int] | None = None


class UserUpdateResponse(BaseModel):
    """Result of updating a user."""

    id: int
    detail: str = "User updated"


class UserDeleteResponse(BaseModel):
    """Result of soft-deleting a user."""

    id: int
    detail: str = "User deactivated"
