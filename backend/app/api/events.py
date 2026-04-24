from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.db.models.security_event import EventHistory, SecurityEvent
from app.db.models.user import User
from app.schemas.security_event import (
    EventDetail,
    EventListResponse,
    EventUpdate,
    HistoryCreate,
    HistoryOut201,
)

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def list_events(
    status: Optional[str] = Query(
        None, description="Comma-separated, e.g. pending,investigating"
    ),
    keyword: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="ISO8601 date, e.g. 2026-03-01"),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(SecurityEvent)

    if status:
        statuses = [s.strip() for s in status.split(",")]
        q = q.filter(SecurityEvent.current_status.in_(statuses))

    if keyword:
        q = q.filter(
            or_(
                SecurityEvent.title.ilike(f"%{keyword}%"),
                SecurityEvent.affected_summary.ilike(f"%{keyword}%"),
            )
        )

    if date_from:
        q = q.filter(SecurityEvent.event_date >= date_from)
    if date_to:
        q = q.filter(SecurityEvent.event_date <= date_to)

    total = q.count()
    items = (
        q.order_by(SecurityEvent.star_rank.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/{event_id}", response_model=EventDetail)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.patch("/{event_id}", response_model=EventDetail)
def update_event(
    event_id: int,
    body: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if body.current_status is not None:
        db.add(
            EventHistory(
                event_id=event.id,
                user_id=current_user.id,
                action="status_change",
                old_status=event.current_status,
                new_status=body.current_status,
            )
        )
        event.current_status = body.current_status

    if body.assignee_user_id is not None:
        db.add(
            EventHistory(
                event_id=event.id,
                user_id=current_user.id,
                action="assign",
            )
        )
        event.assignee_user_id = body.assignee_user_id

    event.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(event)
    return event


@router.post("/{event_id}/history", response_model=HistoryOut201, status_code=201)
def add_history(
    event_id: int,
    body: HistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    action = "resolve" if body.resolved_at else "comment"
    history = EventHistory(
        event_id=event_id,
        user_id=current_user.id,
        action=action,
        note=body.note,
        resolved_at=body.resolved_at,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
