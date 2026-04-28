from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import hash_password
from app.db.session import get_db
from app.db.models.user import Role, User, UserRole
from app.schemas.user import UserCreate, UserItem, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", status_code=200)
def list_users(
    role_id: Optional[int] = Query(None, description="角色職位過濾"),
    keyword: Optional[str] = Query(None, description="姓名或信箱關鍵字"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查詢使用者列表"""
    # Permission check
    _check_manage_accounts(db, current_user)

    q = (
        db.query(User)
        .outerjoin(UserRole, User.id == UserRole.user_id)
        .outerjoin(Role, UserRole.role_id == Role.id)
    )

    if role_id is not None:
        q = q.filter(UserRole.role_id == role_id)

    if keyword:
        q = q.filter(
            (User.name.ilike(f"%{keyword}%")) | (User.email.ilike(f"%{keyword}%"))
        )

    users = q.distinct().order_by(User.id.asc()).all()

    result = []
    for user in users:
        roles = (
            db.query(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .filter(UserRole.user_id == user.id)
            .all()
        )
        result.append(
            UserItem(
                id=user.id,
                name=user.name,
                email=user.email,
                is_active=user.is_active,
                roles=[{"id": r.id, "name": r.name} for r in roles],
            )
        )

    return {"message": "查詢成功", "data": result}


@router.post("", status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新增使用者"""
    # Permission check
    _check_manage_accounts(db, current_user)

    # Validate name length
    if len(body.name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="使用者顯示名稱不可超過 100 字",
        )

    # Validate password length
    if len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密碼最少 8 字元",
        )

    # Validate roles not empty
    if not body.role_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色未設定",
        )

    # Check email uniqueness
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此 Email 已被使用",
        )

    # Create user
    new_user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        is_active=True,
        updated_by=current_user.id,
    )
    db.add(new_user)
    db.flush()  # get new_user.id without commit

    # Create user roles
    for role_id in body.role_ids:
        db.add(UserRole(user_id=new_user.id, role_id=role_id))

    db.commit()
    return {"message": "新增成功"}


@router.patch("/{email}", status_code=200)
def update_user(
    email: str,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新使用者"""
    # Permission check
    _check_manage_accounts(db, current_user)

    # Check user exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在",
        )

    # Validate name if provided
    if body.name is not None and len(body.name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="使用者顯示名稱不可超過 100 字",
        )

    # Validate password if provided
    if body.password is not None and len(body.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密碼至少需要 8 個字元",
        )

    # Validate roles if provided (must not be empty list)
    if body.role_ids is not None and len(body.role_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色不可為空",
        )

    # Apply updates
    if body.name is not None:
        user.name = body.name

    if body.password is not None:
        user.password_hash = hash_password(body.password)

    if body.role_ids is not None:
        db.query(UserRole).filter(UserRole.user_id == user.id).delete()
        for role_id in body.role_ids:
            db.add(UserRole(user_id=user.id, role_id=role_id))

    user.updated_by = current_user.id
    db.commit()
    return {"message": "更新成功"}


@router.delete("/{email}", status_code=200)
def delete_user(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """刪除使用者"""
    # Permission check
    _check_manage_accounts(db, current_user)

    # Check user exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="使用者不存在",
        )

    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無法刪除自己的帳號",
        )

    # Delete user roles first
    db.query(UserRole).filter(UserRole.user_id == user.id).delete()

    # Delete user
    db.delete(user)
    db.commit()
    return {"message": "刪除成功"}


def _check_manage_accounts(db: Session, current_user: User) -> None:
    """Raise 403 if current_user has no can_manage_accounts permission."""
    has_perm = (
        db.query(Role)
        .join(UserRole, Role.id == UserRole.role_id)
        .filter(UserRole.user_id == current_user.id)
        .filter(Role.can_manage_accounts.is_(True))
        .first()
    )
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )
