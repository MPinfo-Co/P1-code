"""/feedback router — 用戶回饋收集 (fn_feedback)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.schema.fn_feedback import FeedbackListItem, FeedbackSubmit
from app.db.connector import get_db
from app.db.models.fn_feedback import Feedback
from app.db.models.function_access import FunctionItems, RoleFunction
from app.db.models.user_role import User, UserRole
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/feedback", tags=["fn_feedback"])

FN_FEEDBACK_CODE = "fn_feedback"

_COMMENT_SUMMARY_MAX = 50


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------


def _has_permission(user_id: int, db: Session) -> bool:
    """Return True if the user has fn_feedback function permission."""
    fn = (
        db.query(FunctionItems)
        .filter(FunctionItems.function_code == FN_FEEDBACK_CODE)
        .first()
    )
    if fn is None:
        return False
    return (
        db.query(RoleFunction)
        .join(UserRole, RoleFunction.role_id == UserRole.role_id)
        .filter(
            UserRole.user_id == user_id,
            RoleFunction.function_id == fn.function_id,
        )
        .first()
        is not None
    )


# ---------------------------------------------------------------------------
# POST /feedback  (fn_feedback_submit_api)
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackSubmit,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Submit user feedback. Requires valid JWT."""
    if payload.rating is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="rating 為必填欄位",
        )
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="rating 須介於 1 至 5 之間",
        )

    feedback = Feedback(
        user_id=auth.user_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    return {"message": "回饋提交成功"}


# ---------------------------------------------------------------------------
# GET /feedback  (fn_feedback_list_api)
# ---------------------------------------------------------------------------


@router.get("", status_code=status.HTTP_200_OK)
def list_feedbacks(
    rating: int | None = Query(None, description="依評分篩選（1–5）"),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """List feedbacks. Requires fn_feedback permission (admin)."""
    if not _has_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無此功能操作權限",
        )

    if rating is not None and (rating < 1 or rating > 5):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="rating 須介於 1 至 5 之間",
        )

    query = (
        db.query(Feedback, User.name.label("user_name"))
        .outerjoin(User, Feedback.user_id == User.id)
        .order_by(Feedback.created_at.desc())
    )
    if rating is not None:
        query = query.filter(Feedback.rating == rating)

    rows = query.all()

    data = []
    for fb, user_name in rows:
        comment = fb.comment
        if comment and len(comment) > _COMMENT_SUMMARY_MAX:
            summary = comment[:_COMMENT_SUMMARY_MAX] + "…"
        else:
            summary = comment

        item = FeedbackListItem(
            id=fb.id,
            user_name=user_name,
            rating=fb.rating,
            comment_summary=summary,
            created_at=fb.created_at,
        )
        data.append(item.model_dump())

    return {"message": "查詢成功", "data": data}
