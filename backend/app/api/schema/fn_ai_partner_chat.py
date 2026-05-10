"""Pydantic schemas for /api/ai-partner-chat endpoints."""

from datetime import datetime

from pydantic import BaseModel


# ── Partners ────────────────────────────────────────────────────────────────

class PartnerItem(BaseModel):
    """單筆 AI 夥伴（供當前角色使用的清單）。"""

    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class PartnersOut(BaseModel):
    """GET /api/ai-partner-chat/partners 回應。"""

    message: str = "查詢成功"
    data: list[PartnerItem]


# ── History ─────────────────────────────────────────────────────────────────

class MessageItem(BaseModel):
    """單筆對話訊息。"""

    role: str
    content: str
    image_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HistoryData(BaseModel):
    """history API 的 data 欄位。"""

    conversation_id: str | None
    messages: list[MessageItem]
    suggestions: list[str]


class HistoryOut(BaseModel):
    """GET /api/ai-partner-chat/history 回應。"""

    message: str = "查詢成功"
    data: HistoryData


# ── Send ─────────────────────────────────────────────────────────────────────

class SendData(BaseModel):
    """send API 的 data 欄位。"""

    content: str
    suggestions: list[str]


class SendOut(BaseModel):
    """POST /api/ai-partner-chat/send 回應（200）。"""

    message: str = "傳送成功"
    data: SendData


# ── New ──────────────────────────────────────────────────────────────────────

class NewRequest(BaseModel):
    """Body for POST /api/ai-partner-chat/new。"""

    partner_id: int


class NewData(BaseModel):
    """new API 的 data 欄位。"""

    conversation_id: str
    messages: list[MessageItem]
    suggestions: list[str]


class NewOut(BaseModel):
    """POST /api/ai-partner-chat/new 回應（201）。"""

    message: str = "新建對話成功"
    data: NewData


# ── Options ──────────────────────────────────────────────────────────────────

class PartnerOptionItem(BaseModel):
    """單筆 AI 夥伴選項（id、name）。"""

    id: int
    name: str

    model_config = {"from_attributes": True}


class OptionsOut(BaseModel):
    """GET /api/ai-partner-chat/options 回應。"""

    message: str = "查詢成功"
    data: list[PartnerOptionItem]
