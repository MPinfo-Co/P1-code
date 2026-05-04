"""/api/user and /api/users routers — user management."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.schema.user import (
    UserCreateOut,
    UserCreateRequest,
    UserDeleteOut,
    UserItem,
    UserListOut,
    UserMeData,
    UserMeResponse,
    UserOptionItem,
    UserOptionsOut,
    UserUpdateOut,
    UserUpdateRequest,
)
from app.db.connector import get_db
from app.db.models.user_role import User, UserRole
from app.db.models.function_access import FunctionItems, RoleFunction
from app.logger_utils import get_system_logger
from app.utils.util_store import AuthContext, authenticate, hash_password

router = APIRouter(prefix="/user", tags=["user"])
system_logger = get_system_logger()

FN_USER_NAME = "fn_user"


@router.get("/me", response_model=UserMeResponse)
def get_me(
    auth: AuthContext = Depends(authenticate),
    db: Session = Depends(get_db),
) -> UserMeResponse:
    """Return the current user's basic info and accessible function list."""
    user = db.query(User).filter(User.id == auth.user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="請重新登入")

    # Collect function_codes via user_roles → role_function → functions (deduplicated)
    function_names = (
        db.query(FunctionItems.function_code)
        .join(RoleFunction, FunctionItems.function_id == RoleFunction.function_id)
        .join(UserRole, RoleFunction.role_id == UserRole.role_id)
        .filter(UserRole.user_id == auth.user_id)
        .distinct()
        .all()
    )
    functions = [row.function_code for row in function_names]

    data = UserMeData(
        id=user.id,
        name=user.name,
        email=user.email,
        functions=functions,
    )
    return UserMeResponse(data=data)


def _has_user_permission(user_id: int, db: Session) -> bool:
    """Return True if the user has fn_user function permission via tb_role_function."""
    fn = db.query(FunctionItems).filter(FunctionItems.function_code == FN_USER_NAME).first()
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


def _collect_role_ids(db: Session, user_ids: list[int]) -> dict[int, list[int]]:
    """Return a `{user_id: [role_id, ...]}` map for the supplied user ids."""
    if not user_ids:
        return {}
    rows = db.query(UserRole).filter(UserRole.user_id.in_(user_ids)).all()
    out: dict[int, list[int]] = {uid: [] for uid in user_ids}
    for row in rows:
        out[row.user_id].append(row.role_id)
    return out


@router.get("", response_model=UserListOut)
def get_user_list(
    role_id: int | None = Query(None, description="Filter to users having this role."),
    keyword: str | None = Query(None, description="LIKE match on name or email."),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> UserListOut:
    """List users in `tb_users`, optionally filtered by role and name/email keyword."""
    if not _has_user_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    query = db.query(User)

    if role_id is not None:
        sub = db.query(UserRole.user_id).filter(UserRole.role_id == role_id).scalar_subquery()
        query = query.filter(User.id.in_(sub))

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))

    rows = query.order_by(User.id.asc()).all()
    role_map = _collect_role_ids(db, [u.id for u in rows])

    items = [
        UserItem(
            id=u.id,
            name=u.name,
            email=u.email,
            role_ids=role_map.get(u.id, []),
            updated_at=u.updated_at,
        )
        for u in rows
    ]
    return UserListOut(data=items)


@router.post("", response_model=UserCreateOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> UserCreateOut:
    """Create a user in `tb_users` and assign roles in `tb_user_roles`."""
    if not _has_user_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密碼最少 8 字元",
        )

    if not payload.role_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色未設定",
        )

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此 Email 已被使用",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        updated_by=auth.user_id,
    )
    db.add(user)
    db.flush()

    for rid in payload.role_ids:
        db.add(UserRole(user_id=user.id, role_id=rid))

    db.commit()
    system_logger.info(f"User {auth.user_id} created user {user.id} ({user.email})")
    return UserCreateOut()


@router.get("/options", response_model=UserOptionsOut)
def get_user_options(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> UserOptionsOut:
    """Return all users as lightweight `[{ id, name }]` for dropdowns."""
    rows = db.query(User).order_by(User.name.asc()).all()
    items = [UserOptionItem(id=u.id, name=u.name) for u in rows]
    return UserOptionsOut(data=items)


@router.patch("/{email}", response_model=UserUpdateOut)
def update_user(
    email: str,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> UserUpdateOut:
    """Update name/password/role_ids on a user identified by email."""
    if not _has_user_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="使用者不存在")

    changes = payload.model_dump(exclude_unset=True)

    if "password" in changes and changes["password"] is not None:
        if len(changes["password"]) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="密碼至少需要 8 個字元",
            )
        user.password_hash = hash_password(changes["password"])

    if "name" in changes and changes["name"] is not None:
        user.name = changes["name"]

    if "role_ids" in changes and changes["role_ids"] is not None:
        if len(changes["role_ids"]) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色不可為空",
            )
        db.query(UserRole).filter(UserRole.user_id == user.id).delete()
        for rid in changes["role_ids"]:
            db.add(UserRole(user_id=user.id, role_id=rid))

    user.updated_by = auth.user_id
    db.commit()
    system_logger.info(f"User {auth.user_id} updated user {user.id} ({email})")
    return UserUpdateOut()


@router.delete("/{email}", response_model=UserDeleteOut)
def delete_user(
    email: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> UserDeleteOut:
    """Delete a user and their role assignments from `tb_users`."""
    if not _has_user_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="使用者不存在")

    # Prevent self-deletion: look up the requesting user's email
    requesting_user = db.query(User).filter(User.id == auth.user_id).first()
    if requesting_user and requesting_user.email == email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無法刪除自己的帳號",
        )

    db.query(UserRole).filter(UserRole.user_id == user.id).delete()
    db.delete(user)
    db.commit()
    system_logger.info(f"User {auth.user_id} deleted user {user.id} ({email})")
    return UserDeleteOut()


