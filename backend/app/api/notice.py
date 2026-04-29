"""/api/notices router — list and create system notices."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schema.notice import NoticeCreate, NoticeCreateOut, NoticeItem, NoticeListOut
from app.db.connector import get_db
from app.db.models import Notice
from app.db.models.fn_user_role import Role, UserRole
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/api/notices", tags=["notice"])


def _has_notice_permission(user_id: int, db: Session) -> bool:
    return (
        db.query(Role)
        .join(UserRole, Role.id == UserRole.role_id)
        .filter(UserRole.user_id == user_id, Role.can_manage_notices.is_(True))
        .first()
        is not None
    )


@router.get("", response_model=NoticeListOut)
def list_notices(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> NoticeListOut:
    """Return notices whose expires_at >= today, ordered by expires_at asc."""
    today = date.today()
    rows = (
        db.query(Notice)
        .filter(Notice.expires_at >= today)
        .order_by(Notice.expires_at.asc())
        .all()
    )
    items = [
        NoticeItem(id=n.id, title=n.title, expires_at=n.expires_at.isoformat())
        for n in rows
    ]
    can_manage = _has_notice_permission(auth.user_id, db)
    return NoticeListOut(data=items, can_manage=can_manage)


@router.post("", response_model=NoticeCreateOut, status_code=status.HTTP_201_CREATED)
def create_notice(
    payload: NoticeCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> NoticeCreateOut:
    """Create a notice; requires fn_notice (can_manage_notices) role permission."""
    if not _has_notice_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="標題未填寫")
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="內容未填寫")
    if not payload.expires_at or not payload.expires_at.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="有效期限未填寫")

    try:
        expires = date.fromisoformat(payload.expires_at)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="有效期限格式錯誤，請使用 YYYY-MM-DD",
        ) from exc

    if expires < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="有效期限須為今日或未來日期",
        )

    notice = Notice(
        title=payload.title.strip(),
        content=payload.content.strip(),
        expires_at=expires,
        created_by=auth.user_id,
    )
    db.add(notice)
    db.commit()
    return NoticeCreateOut()
