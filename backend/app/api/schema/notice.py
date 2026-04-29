"""Pydantic schemas for /api/notices endpoints."""

from pydantic import BaseModel


class NoticeItem(BaseModel):
    """Single notice row returned in the list."""

    id: int
    title: str
    expires_at: str


class NoticeListOut(BaseModel):
    """Response for GET /api/notices."""

    message: str = "查詢成功"
    data: list[NoticeItem]


class NoticeCreate(BaseModel):
    """Body for POST /api/notices."""

    title: str
    content: str
    expires_at: str


class NoticeCreateOut(BaseModel):
    """Response for POST /api/notices (201)."""

    message: str = "新增成功"
