"""Pydantic schemas for fn_company_data endpoints."""

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# GET /api/company-data
# ---------------------------------------------------------------------------


class CompanyDataItem(BaseModel):
    """列表單項。"""

    id: int
    name: str
    content: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# POST /api/company-data
# ---------------------------------------------------------------------------


class CompanyDataCreate(BaseModel):
    """新增公司資料的 Request Body。"""

    name: str
    content: str


# ---------------------------------------------------------------------------
# PATCH /api/company-data/{id}
# ---------------------------------------------------------------------------


class CompanyDataUpdate(BaseModel):
    """更新公司資料的 Request Body。"""

    name: str
    content: str
