"""Pydantic schemas for /api/roles endpoints."""

from pydantic import BaseModel, Field


class RoleFunctionItem(BaseModel):
    """Single function item within a role."""

    function_id: int
    function_code: str


class RoleUserItem(BaseModel):
    """Single user item within a role."""

    id: int
    name: str


class RoleItem(BaseModel):
    """Single role row returned in the list."""

    id: int
    name: str
    users: list[RoleUserItem] = Field(default_factory=list)
    functions: list[RoleFunctionItem] = Field(default_factory=list)


class RoleListOut(BaseModel):
    """Response for GET /api/roles."""

    message: str = "查詢成功"
    data: list[RoleItem]


class RoleAddRequest(BaseModel):
    """Body for POST /api/roles."""

    name: str = Field(..., description="Role name; must be unique.")
    user_ids: list[int] = Field(
        default_factory=list, description="User ids to assign to the role."
    )
    function_ids: list[int] = Field(
        default_factory=list, description="Function ids to grant to the role."
    )


class RoleAddOut(BaseModel):
    """Response for POST /api/roles (201)."""

    message: str = "新增成功"


class RoleUpdateRequest(BaseModel):
    """Body for PATCH /api/roles/{name} — all fields optional."""

    name: str | None = Field(None, description="New role name.")
    user_ids: list[int] | None = None
    function_ids: list[int] | None = None


class RoleUpdateOut(BaseModel):
    """Response for PATCH /api/roles/{name} (200)."""

    message: str = "更新成功"


class RoleDelOut(BaseModel):
    """Response for DELETE /api/roles/{name} (200)."""

    message: str = "刪除成功"


class FunctionOptionItem(BaseModel):
    """Single item in the function options list."""

    function_id: int
    function_code: str
    function_label: str


class FunctionOptionsOut(BaseModel):
    """Response for GET /api/functions/options."""

    message: str = "查詢成功"
    data: list[FunctionOptionItem]
