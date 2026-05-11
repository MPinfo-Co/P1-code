"""Pydantic schemas for /events endpoints."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventSummary(BaseModel):
    """Compact row used for the events list view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_date: date
    date_end: date | None = None
    star_rank: int
    title: str
    affected_summary: str
    current_status: str
    detection_count: int
    assignee_user_id: int | None = None
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    """Paginated event list."""

    items: list[EventSummary]
    page: int
    page_size: int
    total: int
    total_pages: int


class EventDetail(BaseModel):
    """Full event payload for the detail view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_date: date
    date_end: date | None
    star_rank: int
    title: str
    description: str | None
    affected_summary: str
    affected_detail: str | None
    current_status: str
    match_key: str
    detection_count: int
    continued_from: int | None
    assignee_user_id: int | None
    suggests: list[Any] | None
    logs: list[Any] | None
    ioc_list: list[Any] | None
    mitre_tags: list[Any] | None
    created_at: datetime
    updated_at: datetime


class EventUpdateRequest(BaseModel):
    """Patch payload for `PATCH /events/{event_id}`."""

    current_status: str | None = Field(
        None, description="New status, e.g. pending|investigating|resolved|closed."
    )
    assignee_user_id: int | None = Field(
        None, description="User id to assign the event to. Pass null to unassign."
    )


class EventHistoryEntry(BaseModel):
    """One row of `tb_event_history`."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    user_id: int
    action: str
    old_status: str | None
    new_status: str | None
    note: str | None
    resolved_at: datetime | None
    created_at: datetime


class EventHistoryListResponse(BaseModel):
    """Chronological history for one event."""

    items: list[EventHistoryEntry]


class EventHistoryCreateRequest(BaseModel):
    """Body for `POST /events/{event_id}/history`."""

    action: str = Field(..., description="e.g. comment|status_change|assign.")
    old_status: str | None = None
    new_status: str | None = None
    note: str | None = None
    resolved_at: datetime | None = None


class EventHistoryCreateResponse(BaseModel):
    """Result of inserting one history row."""

    id: int
    event_id: int
