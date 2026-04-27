from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models.user import Role, User
from app.db.session import get_db

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("/options")
def list_role_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """對應 fn_role_options_api：回傳所有角色 id + name，供下拉選單使用。"""
    roles = db.query(Role).order_by(Role.name).all()
    return {
        "message": "查詢成功",
        "data": [{"id": r.id, "name": r.name} for r in roles],
    }
