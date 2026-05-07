"""/api/roles router — role management (fn_role)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.schema.roles import (
    RoleAddRequest,
    RoleAddOut,
    RoleDelOut,
    RoleFunctionItem,
    RoleItem,
    RoleListOut,
    RoleUpdateRequest,
    RoleUpdateOut,
)
from app.db.connector import get_db
from app.db.models.function_access import FunctionItems, RoleFunction
from app.db.models.user_role import Role, User, UserRole
from app.logger_utils import get_system_logger
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/roles", tags=["roles"])
system_logger = get_system_logger()

FN_ROLE_NAME = "fn_role"
FN_USER_NAME = "fn_user"


def _has_fn_role_permission(user_id: int, db: Session) -> bool:
    """Return True if the user has fn_role function permission via tb_role_function."""
    fn = (
        db.query(FunctionItems)
        .filter(FunctionItems.function_code == FN_ROLE_NAME)
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


@router.get("", response_model=RoleListOut)
def list_roles(
    keyword: str | None = Query(None, description="Filter by role name (ILIKE)."),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> RoleListOut:
    """List roles, optionally filtered by keyword. Requires fn_role permission."""
    if not _has_fn_role_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    query = db.query(Role)
    if keyword:
        query = query.filter(Role.name.ilike(f"%{keyword}%"))
    roles = query.order_by(Role.created_at.asc()).all()

    items = []
    for role in roles:
        # Get members
        user_rows = (
            db.query(User)
            .join(UserRole, User.id == UserRole.user_id)
            .filter(UserRole.role_id == role.id)
            .all()
        )
        users = [{"id": u.id, "name": u.name} for u in user_rows]

        # Get functions
        fn_rows = (
            db.query(FunctionItems)
            .join(RoleFunction, FunctionItems.function_id == RoleFunction.function_id)
            .filter(RoleFunction.role_id == role.id)
            .all()
        )
        functions = [
            RoleFunctionItem(function_id=f.function_id, function_code=f.function_code)
            for f in fn_rows
        ]

        items.append(
            RoleItem(
                id=role.id,
                name=role.name,
                users=users,
                functions=functions,
            )
        )
    return RoleListOut(data=items)


@router.post("", response_model=RoleAddOut, status_code=status.HTTP_201_CREATED)
def add_role(
    payload: RoleAddRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> RoleAddOut:
    """Create a new role with optional members and function assignments."""
    if not _has_fn_role_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名稱未填寫",
        )

    if db.query(Role).filter(Role.name == payload.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此角色名稱已存在",
        )

    role = Role(name=payload.name)
    db.add(role)
    db.flush()

    for uid in payload.user_ids or []:
        db.add(UserRole(user_id=uid, role_id=role.id))

    for fid in payload.function_ids or []:
        db.add(RoleFunction(role_id=role.id, function_id=fid))

    db.commit()
    system_logger.info(f"User {auth.user_id} created role {role.id} ({role.name})")
    return RoleAddOut()


@router.patch("/{name}", response_model=RoleUpdateOut)
def update_role(
    name: str,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> RoleUpdateOut:
    """Update a role's name, members, or function assignments."""
    if not _has_fn_role_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    role = db.query(Role).filter(Role.name == name).first()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    changes = payload.model_dump(exclude_unset=True)

    if "name" in changes and changes["name"] is not None:
        # Check uniqueness against other roles
        conflict = (
            db.query(Role)
            .filter(Role.name == changes["name"], Role.id != role.id)
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此角色名稱已被其他角色使用",
            )
        role.name = changes["name"]

    if "user_ids" in changes and changes["user_ids"] is not None:
        db.query(UserRole).filter(UserRole.role_id == role.id).delete()
        for uid in changes["user_ids"]:
            db.add(UserRole(user_id=uid, role_id=role.id))

    if "function_ids" in changes and changes["function_ids"] is not None:
        db.query(RoleFunction).filter(RoleFunction.role_id == role.id).delete()
        for fid in changes["function_ids"]:
            db.add(RoleFunction(role_id=role.id, function_id=fid))

    db.commit()
    system_logger.info(f"User {auth.user_id} updated role {role.id} ({role.name})")
    return RoleUpdateOut()


@router.delete("/{name}", response_model=RoleDelOut)
def delete_role(
    name: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> RoleDelOut:
    """Delete a role and all related user/function associations."""
    if not _has_fn_role_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    role = db.query(Role).filter(Role.name == name).first()
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    db.query(RoleFunction).filter(RoleFunction.role_id == role.id).delete()
    db.query(UserRole).filter(UserRole.role_id == role.id).delete()
    db.delete(role)
    db.commit()
    system_logger.info(f"User {auth.user_id} deleted role ({name})")
    return RoleDelOut()


@router.get("/options", response_model=None)
def get_role_options(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
):
    """Return all roles as lightweight [{ id, name }] for dropdowns."""
    rows = db.query(Role).order_by(Role.name.asc()).all()
    items = [{"id": r.id, "name": r.name} for r in rows]
    return {"message": "查詢成功", "data": items}
