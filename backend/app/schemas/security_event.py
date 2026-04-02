from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel


class HistoryOut(BaseModel):
    id: int
    user_id: int
    action: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    note: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventItem(BaseModel):
    id: int
    event_date: date
    date_end: Optional[date] = None
    star_rank: int
    title: str
    affected_summary: str
    detection_count: int
    current_status: str
    assignee_user_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventDetail(EventItem):
    description: Optional[str] = None
    affected_detail: Optional[str] = None
    match_key: str
    continued_from: Optional[int] = None
    suggests: Optional[list[Any]] = None
    logs: Optional[list[Any]] = None
    ioc_list: Optional[list[Any]] = None
    mitre_tags: Optional[list[Any]] = None
    updated_at: datetime
    history: list[HistoryOut] = []


class EventListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[EventItem]


class EventUpdate(BaseModel):
    current_status: Optional[str] = None
    assignee_user_id: Optional[int] = None


class HistoryCreate(BaseModel):
    note: str
    resolved_at: Optional[datetime] = None


class HistoryOut201(HistoryOut):
    event_id: int
