from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import hash_password
from app.db.models.user import Role, User, UserRole
from app.db.session import get_db
from app.schemas.user import UserCreate, UserItem, UserListResponse, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


def _require_manage_accounts(current_user: User) -> None:
    """檢查使用者是否具有 can_manage_accounts 權限"""
    from app.db.models.user import UserRole, Role  # noqa: F401

    if not hasattr(current_user, "_has_manage_accounts"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )


def _get_user_items(db: Session, users: list[User]) -> list[UserItem]:
    """將 User ORM 物件轉換為 UserItem，附帶角色資訊"""
    result = []
    for user in users:
        user_roles = (
            db.query(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user.id)
            .all()
        )
        item = UserItem(
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            roles=[{"id": r.id, "name": r.name} for r in user_roles],
        )
        result.append(item)
    return result


def _check_manage_accounts(current_user: User, db: Session) -> None:
    """確認當前使用者具有 can_manage_accounts 權限"""
    roles = (
        db.query(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == current_user.id)
        .all()
    )
    has_permission = any(r.can_manage_accounts for r in roles)
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )


@router.get("", response_model=UserListResponse)
def list_users(
    role_id: Optional[int] = Query(None, description="角色職位 ID"),
    keyword: Optional[str] = Query(None, description="關鍵字，過濾姓名或信箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_manage_accounts(current_user, db)

    q = db.query(User)

    if role_id is not None:
        q = q.join(UserRole, UserRole.user_id == User.id).filter(
            UserRole.role_id == role_id
        )

    if keyword:
        q = q.filter(
            User.name.ilike(f"%{keyword}%") | User.email.ilike(f"%{keyword}%")
        )

    users = q.order_by(User.created_at.asc()).all()
    items = _get_user_items(db, users)
    return UserListResponse(data=items)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_manage_accounts(current_user, db)

    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="此 Email 已被使用")

    new_user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        is_active=True,
    )
    db.add(new_user)
    db.flush()

    for rid in body.role_ids:
        db.add(UserRole(user_id=new_user.id, role_id=rid))

    db.commit()
    return {"message": "新增成功"}


@router.patch("/{email}")
def update_user(
    email: str,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_manage_accounts(current_user, db)

    target = db.query(User).filter(User.email == email).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="使用者不存在")

    if body.name is not None:
        target.name = body.name

    if body.password is not None:
        target.password_hash = hash_password(body.password)

    if body.role_ids is not None:
        db.query(UserRole).filter(UserRole.user_id == target.id).delete()
        for rid in body.role_ids:
            db.add(UserRole(user_id=target.id, role_id=rid))

    db.commit()
    return {"message": "更新成功"}


@router.delete("/{email}")
def delete_user(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_manage_accounts(current_user, db)

    target = db.query(User).filter(User.email == email).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="使用者不存在")

    if target.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無法刪除自己的帳號")

    db.query(UserRole).filter(UserRole.user_id == target.id).delete()
    db.delete(target)
    db.commit()
    return {"message": "刪除成功"}
