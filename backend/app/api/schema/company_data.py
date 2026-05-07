"""Pydantic schemas for fn_company_data endpoints."""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared sub-schemas
# ---------------------------------------------------------------------------


class PartnerItem(BaseModel):
    """單筆 AI 夥伴資訊（id + name）。"""

    id: int
    name: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# GET /api/company-data
# ---------------------------------------------------------------------------


class CompanyDataItem(BaseModel):
    """列表單項：公司資料 + 已關聯的 AI 夥伴清單。"""

    id: int
    name: str
    content: str
    partners: list[PartnerItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# POST /api/company-data
# ---------------------------------------------------------------------------


class CompanyDataCreate(BaseModel):
    """新增公司資料的 Request Body。"""

    name: str
    content: str
    partner_ids: list[int] = Field(
        default_factory=list, description="適用夥伴的 partner_id 清單"
    )


# ---------------------------------------------------------------------------
# PATCH /api/company-data/{id}
# ---------------------------------------------------------------------------


class CompanyDataUpdate(BaseModel):
    """更新公司資料的 Request Body。"""

    name: str
    content: str
    partner_ids: list[int] = Field(
        default_factory=list, description="適用夥伴的 partner_id 清單"
    )


# ---------------------------------------------------------------------------
# GET /api/company-data/partner-options
# ---------------------------------------------------------------------------


class PartnerOptionItem(BaseModel):
    """夥伴下拉選項單項。"""

    id: int
    name: str

    model_config = {"from_attributes": True}
