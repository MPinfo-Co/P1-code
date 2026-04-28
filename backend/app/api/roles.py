from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.db.models.user import Role, User
from app.schemas.user import RoleOptionItem

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("/options", status_code=200)
def get_role_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得角色選項清單"""
    roles = db.query(Role).order_by(Role.name.asc()).all()
    data = [RoleOptionItem(id=r.id, name=r.name) for r in roles]
    return {"message": "查詢成功", "data": data}
