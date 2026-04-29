"""/user router — list, create, update, and soft-delete users."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.schema.user import (
    UserCreateRequest,
    UserCreateResponse,
    UserDeleteResponse,
    UserListResponse,
    UserSummary,
    UserUpdateRequest,
    UserUpdateResponse,
)
from app.db.connector import get_db
from app.db.models import User, UserRole
from app.logger_utils import get_system_logger
from app.utils.util_store import AuthContext, authenticate, hash_password

router = APIRouter(prefix="/user", tags=["user"])
system_logger = get_system_logger()


def _collect_role_ids(db: Session, user_ids: list[int]) -> dict[int, list[int]]:
    """Return a `{user_id: [role_id, ...]}` map for the supplied user ids."""
    if not user_ids:
        return {}
    rows = db.query(UserRole).filter(UserRole.user_id.in_(user_ids)).all()
    out: dict[int, list[int]] = {uid: [] for uid in user_ids}
    for row in rows:
        out[row.user_id].append(row.role_id)
    return out


@router.get("", response_model=UserListResponse)
def get_user_list(
    role_id: int | None = Query(None, description="Filter to users having this role."),
    keyword: str | None = Query(None, description="LIKE match on name or email."),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> UserListResponse:
    """List users in `tb_users`, optionally filtered by role and name/email keyword."""
    query = db.query(User)

    if role_id is not None:
        sub = db.query(UserRole.user_id).filter(UserRole.role_id == role_id).subquery()
        query = query.filter(User.id.in_(sub))

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(or_(User.name.ilike(like), User.email.ilike(like)))

    rows = query.order_by(User.id.asc()).all()
    role_map = _collect_role_ids(db, [u.id for u in rows])

    items = [
        UserSummary(
            id=u.id,
            name=u.name,
            email=u.email,
            is_active=u.is_active,
            role_ids=role_map.get(u.id, []),
            updated_at=u.updated_at,
        )
        for u in rows
    ]
    return UserListResponse(items=items, total=len(items))


@router.post("", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> UserCreateResponse:
    """Create a user in `tb_users` and assign roles in `tb_user_roles`."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_active=True,
        updated_by=auth.user_id,
    )
    db.add(user)
    db.flush()

    for rid in payload.role_ids:
        db.add(UserRole(user_id=user.id, role_id=rid))

    db.commit()
    db.refresh(user)
    system_logger.info(f"User {auth.user_id} created user {user.id} ({user.email})")
    return UserCreateResponse(id=user.id, name=user.name, email=user.email)


def _apply_user_changes(user: User, changes: dict, db: Session) -> None:
    """Apply name/email/password/role_ids changes to `user` in place."""
    if "name" in changes:
        user.name = changes["name"]
    if "email" in changes:
        user.email = changes["email"]
    if "password" in changes:
        user.password_hash = hash_password(changes["password"])
    if "role_ids" in changes:
        db.query(UserRole).filter(UserRole.user_id == user.id).delete()
        for rid in changes["role_ids"]:
            db.add(UserRole(user_id=user.id, role_id=rid))


@router.patch("/{user_id}", response_model=UserUpdateResponse)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> UserUpdateResponse:
    """Update name/email/password/role_ids on a user; all fields are optional."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updatable fields supplied.",
        )

    new_email = changes.get("email")
    if new_email and new_email != user.email:
        if db.query(User).filter(User.email == new_email).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered.",
            )

    _apply_user_changes(user, changes, db)
    user.updated_by = auth.user_id

    db.commit()
    system_logger.info(f"User {auth.user_id} updated user {user_id}")
    return UserUpdateResponse(id=user_id)


@router.delete("/{user_id}", response_model=UserDeleteResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> UserDeleteResponse:
    """Soft-delete a user by setting `is_active=False` on `tb_users`."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    user.updated_by = auth.user_id
    db.commit()
    system_logger.info(f"User {auth.user_id} deactivated user {user_id}")
    return UserDeleteResponse(id=user_id)
