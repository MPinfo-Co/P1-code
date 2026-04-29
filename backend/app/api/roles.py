from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.db.models.user import Function, Role, RoleFunction, User, UserRole
from app.schemas.role import RoleCreate, RoleItem, RoleUpdate
from app.schemas.user import RoleOptionItem

router = APIRouter(prefix="/api/roles", tags=["roles"])


# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------


def _check_fn_role(db: Session, current_user: User) -> None:
    """Raise 403 if current_user's roles do not include fn_role function."""
    has_perm = (
        db.query(RoleFunction)
        .join(UserRole, RoleFunction.role_id == UserRole.role_id)
        .join(Function, RoleFunction.function_id == Function.function_id)
        .filter(UserRole.user_id == current_user.id)
        .filter(Function.function_name == "fn_role")
        .first()
    )
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )


# ---------------------------------------------------------------------------
# GET /api/roles/options  (no fn_role permission required, just login)
# ---------------------------------------------------------------------------


@router.get("/options", status_code=200)
def get_role_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得角色選項清單"""
    roles = db.query(Role).order_by(Role.name.asc()).all()
    data = [RoleOptionItem(id=r.id, name=r.name) for r in roles]
    return {"message": "查詢成功", "data": data}


# ---------------------------------------------------------------------------
# GET /api/roles
# ---------------------------------------------------------------------------


@router.get("", status_code=200)
def list_roles(
    keyword: Optional[str] = Query(None, description="角色名稱關鍵字"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查詢角色列表"""
    _check_fn_role(db, current_user)

    q = db.query(Role)
    if keyword:
        q = q.filter(Role.name.ilike(f"%{keyword}%"))
    roles = q.order_by(Role.created_at.asc()).all()

    result = []
    for role in roles:
        users = (
            db.query(User)
            .join(UserRole, User.id == UserRole.user_id)
            .filter(UserRole.role_id == role.id)
            .all()
        )
        functions = (
            db.query(Function)
            .join(RoleFunction, Function.function_id == RoleFunction.function_id)
            .filter(RoleFunction.role_id == role.id)
            .all()
        )
        result.append(
            RoleItem(
                id=role.id,
                name=role.name,
                users=[{"id": u.id, "name": u.name} for u in users],
                functions=[
                    {"function_id": f.function_id, "function_name": f.function_name}
                    for f in functions
                ],
            )
        )

    return {"message": "查詢成功", "data": result}


# ---------------------------------------------------------------------------
# POST /api/roles
# ---------------------------------------------------------------------------


@router.post("", status_code=201)
def create_role(
    body: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新增角色"""
    _check_fn_role(db, current_user)

    if not body.name or not body.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名稱未填寫",
        )

    existing = db.query(Role).filter(Role.name == body.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此角色名稱已存在",
        )

    new_role = Role(name=body.name)
    db.add(new_role)
    db.flush()

    if body.user_ids:
        for user_id in body.user_ids:
            db.add(UserRole(user_id=user_id, role_id=new_role.id))

    if body.function_ids:
        for function_id in body.function_ids:
            db.add(RoleFunction(role_id=new_role.id, function_id=function_id))

    db.commit()
    return {"message": "新增成功"}


# ---------------------------------------------------------------------------
# PATCH /api/roles/{name}
# ---------------------------------------------------------------------------


@router.patch("/{name}", status_code=200)
def update_role(
    name: str,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新角色"""
    _check_fn_role(db, current_user)

    role = db.query(Role).filter(Role.name == name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在",
        )

    if body.name is not None:
        conflict = (
            db.query(Role).filter(Role.name == body.name, Role.id != role.id).first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此角色名稱已被其他角色使用",
            )
        role.name = body.name

    if body.user_ids is not None:
        db.query(UserRole).filter(UserRole.role_id == role.id).delete()
        for user_id in body.user_ids:
            db.add(UserRole(user_id=user_id, role_id=role.id))

    if body.function_ids is not None:
        db.query(RoleFunction).filter(RoleFunction.role_id == role.id).delete()
        for function_id in body.function_ids:
            db.add(RoleFunction(role_id=role.id, function_id=function_id))

    db.commit()
    return {"message": "更新成功"}


# ---------------------------------------------------------------------------
# DELETE /api/roles/{name}
# ---------------------------------------------------------------------------


@router.delete("/{name}", status_code=200)
def delete_role(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """刪除角色"""
    _check_fn_role(db, current_user)

    role = db.query(Role).filter(Role.name == name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在",
        )

    db.query(RoleFunction).filter(RoleFunction.role_id == role.id).delete()
    db.query(UserRole).filter(UserRole.role_id == role.id).delete()
    db.delete(role)
    db.commit()
    return {"message": "刪除成功"}
