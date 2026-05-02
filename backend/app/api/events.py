"""/events router — list, fetch, update, and append history for security events."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.schema.events import (
    EventDetail,
    EventHistoryCreateRequest,
    EventHistoryCreateResponse,
    EventHistoryEntry,
    EventHistoryListResponse,
    EventListResponse,
    EventSummary,
    EventUpdateRequest,
)
from app.db.connector import get_db
from app.db.models import EventHistory, SecurityEvent
from app.utils.util_store import AuthContext, authenticate, parse_iso_date

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def list_events(
    status_filter: str | None = Query(
        None,
        alias="status",
        description="Comma-separated, e.g. pending,investigating",
    ),
    keyword: str | None = Query(None, description="Substring match on title or affected_summary."),
    date_from: str | None = Query(None, description="ISO8601 date, e.g. 2026-03-01"),
    date_to: str | None = Query(None, description="ISO8601 date, inclusive."),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> EventListResponse:
    """Query `tb_security_events` rows that match the supplied filters."""
    query = db.query(SecurityEvent)

    if status_filter:
        statuses = [s.strip() for s in status_filter.split(",") if s.strip()]
        if statuses:
            query = query.filter(SecurityEvent.current_status.in_(statuses))

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                SecurityEvent.title.ilike(like),
                SecurityEvent.affected_summary.ilike(like),
            )
        )

    if date_from:
        query = query.filter(SecurityEvent.event_date >= parse_iso_date(date_from, "date_from"))
    if date_to:
        query = query.filter(SecurityEvent.event_date <= parse_iso_date(date_to, "date_to"))

    total = query.count()
    rows = (
        query.order_by(SecurityEvent.event_date.desc(), SecurityEvent.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return EventListResponse(
        items=[EventSummary.model_validate(r) for r in rows],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{event_id}", response_model=EventDetail)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> EventDetail:
    """Get a single event from `tb_security_events` by id."""
    event = db.get(SecurityEvent, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return EventDetail.model_validate(event)


@router.patch("/{event_id}", response_model=EventDetail)
def update_event(
    event_id: int,
    payload: EventUpdateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> EventDetail:
    """Update `current_status` and/or `assignee_user_id` on a security event."""
    event = db.get(SecurityEvent, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updatable fields supplied.",
        )

    for field, value in changes.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)
    return EventDetail.model_validate(event)


@router.get("/{event_id}/history", response_model=EventHistoryListResponse)
def list_history(
    event_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> EventHistoryListResponse:
    """Get the processing log for one event from `tb_event_history`."""

    if db.get(SecurityEvent, event_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    rows = (
        db.query(EventHistory)
        .filter(EventHistory.event_id == event_id)
        .order_by(EventHistory.created_at.asc(), EventHistory.id.asc())
        .all()
    )
    return EventHistoryListResponse(items=[EventHistoryEntry.model_validate(r) for r in rows])


@router.post(
    "/{event_id}/history",
    response_model=EventHistoryCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_history(
    event_id: int,
    payload: EventHistoryCreateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> EventHistoryCreateResponse:
    """Append one row to `tb_event_history` for the given event."""
    if db.get(SecurityEvent, event_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    entry = EventHistory(
        event_id=event_id,
        user_id=auth.user_id,
        action=payload.action,
        old_status=payload.old_status,
        new_status=payload.new_status,
        note=payload.note,
        resolved_at=payload.resolved_at,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return EventHistoryCreateResponse(id=entry.id, event_id=entry.event_id)
