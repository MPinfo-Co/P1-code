"""Pydantic schemas for /api/settings endpoints."""

from pydantic import BaseModel


class SystemParamItem(BaseModel):
    """Single system param row returned in the list."""

    param_type: str
    param_code: str
    param_value: str

    model_config = {"from_attributes": True}


class SystemParamListResponse(BaseModel):
    """Response for GET /api/settings."""

    message: str = "查詢成功"
    data: list[SystemParamItem]


class SystemParamUpdate(BaseModel):
    """Body for PATCH /api/settings/{param_code}."""

    param_value: str


class SystemParamUpdateResponse(BaseModel):
    """Response for PATCH /api/settings/{param_code} (200)."""

    message: str = "更新成功"


class ParamTypeOptionsResponse(BaseModel):
    """Response for GET /api/settings/options/param-types."""

    message: str = "查詢成功"
    data: list[str]
