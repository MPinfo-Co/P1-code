"""/api/roles router — role option helpers."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.connector import get_db
from app.db.models import Role
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/api/roles", tags=["roles"])


class RoleOption(BaseModel):
    id: int
    name: str


@router.get("/options", response_model=list[RoleOption])
def get_role_options(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> list[RoleOption]:
    """回傳所有角色的 id + name，供下拉選單使用。"""
    roles = db.query(Role).order_by(Role.id.asc()).all()
    return [RoleOption(id=r.id, name=r.name) for r in roles]
