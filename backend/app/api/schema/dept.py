"""Pydantic schemas for /api/dept endpoints."""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------


class DeptItem(BaseModel):
    """Single department row in list response."""

    model_config = {"from_attributes": True}

    id: int
    name: str
    code: str
    parent_id: int | None
    manager_id: int | None
    is_active: bool


class DeptListResponse(BaseModel):
    """Response for GET /api/dept."""

    message: str = "查詢成功"
    data: dict


# ---------------------------------------------------------------------------
# Query (list with pagination)
# ---------------------------------------------------------------------------


class DeptListData(BaseModel):
    """Paginated data payload."""

    items: list[DeptItem]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class DeptCreate(BaseModel):
    """Body for POST /api/dept."""

    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    parent_id: int | None = None
    manager_id: int | None = None


class DeptCreateOut(BaseModel):
    """Response for POST /api/dept (201)."""

    message: str = "新增成功"


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class DeptUpdate(BaseModel):
    """Body for PATCH /api/dept/{id}."""

    name: str | None = Field(None, min_length=1, max_length=100)
    code: str | None = Field(None, min_length=1, max_length=50)
    parent_id: int | None = None
    manager_id: int | None = None


class DeptUpdateOut(BaseModel):
    """Response for PATCH /api/dept/{id}."""

    message: str = "更新成功"


# ---------------------------------------------------------------------------
# Toggle
# ---------------------------------------------------------------------------


class DeptToggle(BaseModel):
    """Body for PATCH /api/dept/{id}/toggle."""

    is_active: bool


class DeptToggleOut(BaseModel):
    """Response for PATCH /api/dept/{id}/toggle."""

    message: str


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


class MemberItem(BaseModel):
    """Single member in department members response."""

    id: int
    name: str


class DeptMembersOut(BaseModel):
    """Response for GET /api/dept/{id}/members."""

    message: str = "查詢成功"
    data: list[MemberItem]


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


class DeptOptionItem(BaseModel):
    """Single department option for dropdown."""

    id: int
    name: str


class DeptOptionsOut(BaseModel):
    """Response for GET /api/dept/options."""

    message: str = "查詢成功"
    data: list[DeptOptionItem]
