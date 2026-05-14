"""Pydantic schemas for /api/home endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


# ── Partners ────────────────────────────────────────────────────────────────


class HomePartnerItem(BaseModel):
    """首頁單筆 AI 夥伴（含最愛狀態）。"""

    id: int
    name: str
    description: str | None = None
    is_favorite: bool

    model_config = {"from_attributes": True}


class HomePartnersOut(BaseModel):
    """GET /api/home/partners 回應。"""

    message: str = "查詢成功"
    data: list[HomePartnerItem]


# ── Favorite Toggle ──────────────────────────────────────────────────────────


class FavoriteToggleRequest(BaseModel):
    """Body for POST /api/home/favorite/toggle。"""

    partner_id: Optional[int] = None


class FavoriteToggleData(BaseModel):
    """toggle API 的 data 欄位。"""

    partner_id: int
    is_favorite: bool


class FavoriteToggleOut(BaseModel):
    """POST /api/home/favorite/toggle 回應。"""

    message: str
    data: FavoriteToggleData
