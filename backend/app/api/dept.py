"""/api/dept router — department management CRUD."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.schema.dept import (
    DeptCreate,
    DeptCreateOut,
    DeptListData,
    DeptItem,
    DeptMembersOut,
    DeptOptionItem,
    DeptOptionsOut,
    DeptToggle,
    DeptToggleOut,
    DeptUpdate,
    DeptUpdateOut,
    MemberItem,
)
from app.db.connector import get_db
from app.db.models.fn_dept import Department
from app.db.models.fn_user_role import Role, User, UserRole
from app.logger_utils import get_system_logger
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/api/dept", tags=["dept"])
system_logger = get_system_logger()

_ALLOWED_PAGE_SIZES = {10, 25, 50}


def _has_dept_permission(user_id: int, db: Session) -> bool:
    """Return True if the user has can_manage_depts permission."""
    return (
        db.query(Role)
        .join(UserRole, Role.id == UserRole.role_id)
        .filter(UserRole.user_id == user_id, Role.can_manage_depts.is_(True))
        .first()
        is not None
    )


def _dept_depth(dept: Department, db: Session) -> int:
    """Return the 1-based depth level of a department (root = 1)."""
    depth = 1
    current = dept
    while current.parent_id is not None:
        current = db.get(Department, current.parent_id)
        if current is None:
            break
        depth += 1
    return depth


# ---------------------------------------------------------------------------
# GET /api/dept/options  — must come before /{id} to avoid conflict
# ---------------------------------------------------------------------------


@router.get("/options", response_model=DeptOptionsOut)
def get_dept_options(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> DeptOptionsOut:
    """Return active departments whose depth is less than 3 (can still add children)."""
    rows = db.query(Department).filter(Department.is_active.is_(True)).all()
    items = [
        DeptOptionItem(id=d.id, name=d.name)
        for d in rows
        if _dept_depth(d, db) < 3
    ]
    return DeptOptionsOut(data=items)


# ---------------------------------------------------------------------------
# GET /api/dept
# ---------------------------------------------------------------------------


@router.get("")
def list_depts(
    keyword: str | None = Query(None, description="Filter by name or code."),
    page: int = Query(1, description="Page number (>= 1)."),
    page_size: int = Query(10, description="Items per page: 10, 25, or 50."),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Query tb_departments with optional keyword filter and pagination."""
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="頁碼不可小於 1")
    if page_size not in _ALLOWED_PAGE_SIZES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="每頁筆數僅允許 10、25 或 50",
        )
    if not _has_dept_permission(auth.user_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您沒有執行此操作的權限")

    query = db.query(Department)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            Department.name.ilike(like) | Department.code.ilike(like)
        )

    total = query.count()
    rows = (
        query.order_by(Department.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [
        DeptItem(
            id=d.id,
            name=d.name,
            code=d.code,
            parent_id=d.parent_id,
            manager_id=d.manager_id,
            is_active=d.is_active,
        )
        for d in rows
    ]
    data = DeptListData(items=items, total=total, page=page, page_size=page_size)
    return {"message": "查詢成功", "data": data.model_dump()}


# ---------------------------------------------------------------------------
# POST /api/dept
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DeptCreateOut)
def create_dept(
    payload: DeptCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> DeptCreateOut:
    """Create a new department."""
    if not _has_dept_permission(auth.user_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您沒有執行此操作的權限")

    # Check code uniqueness
    if db.query(Department).filter(Department.code == payload.code).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="此部門代碼已被使用")

    # Check parent depth
    if payload.parent_id is not None:
        parent = db.get(Department, payload.parent_id)
        if parent is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="上級部門不存在")
        parent_depth = _dept_depth(parent, db)
        if parent_depth >= 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="部門層級最多 3 層，無法在此部門下新增子部門",
            )

    dept = Department(
        name=payload.name,
        code=payload.code,
        parent_id=payload.parent_id,
        manager_id=payload.manager_id,
        is_active=True,
    )
    db.add(dept)
    db.commit()
    system_logger.info(f"User {auth.user_id} created department {dept.id} ({dept.code})")
    return DeptCreateOut()


# ---------------------------------------------------------------------------
# PATCH /api/dept/{dept_id}
# ---------------------------------------------------------------------------


@router.patch("/{dept_id}", response_model=DeptUpdateOut)
def update_dept(
    dept_id: int,
    payload: DeptUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> DeptUpdateOut:
    """Update an existing department."""
    if not _has_dept_permission(auth.user_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您沒有執行此操作的權限")

    dept = db.get(Department, dept_id)
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部門不存在")

    if payload.code is not None and payload.code != dept.code:
        existing = db.query(Department).filter(Department.code == payload.code).first()
        if existing and existing.id != dept_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="此部門代碼已被使用")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(dept, field, value)

    db.commit()
    system_logger.info(f"User {auth.user_id} updated department {dept_id}")
    return DeptUpdateOut()


# ---------------------------------------------------------------------------
# PATCH /api/dept/{dept_id}/toggle
# ---------------------------------------------------------------------------


@router.patch("/{dept_id}/toggle", response_model=DeptToggleOut)
def toggle_dept(
    dept_id: int,
    payload: DeptToggle,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> DeptToggleOut:
    """Enable or disable a department."""
    if not _has_dept_permission(auth.user_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您沒有執行此操作的權限")

    dept = db.get(Department, dept_id)
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部門不存在")

    # If disabling, check for active members
    if not payload.is_active:
        member_count = db.query(User).filter(User.department_id == dept_id).count()
        if member_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="此部門仍有人員，無法停用"
            )

    dept.is_active = payload.is_active
    db.commit()
    msg = "啟用成功" if payload.is_active else "停用成功"
    system_logger.info(f"User {auth.user_id} toggled department {dept_id} is_active={payload.is_active}")
    return DeptToggleOut(message=msg)


# ---------------------------------------------------------------------------
# GET /api/dept/{dept_id}/members
# ---------------------------------------------------------------------------


@router.get("/{dept_id}/members", response_model=DeptMembersOut)
def get_dept_members(
    dept_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> DeptMembersOut:
    """Return the list of members in the specified department."""
    if not _has_dept_permission(auth.user_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您沒有執行此操作的權限")

    dept = db.get(Department, dept_id)
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部門不存在")

    members = db.query(User).filter(User.department_id == dept_id).all()
    items = [MemberItem(id=u.id, name=u.name) for u in members]
    return DeptMembersOut(data=items)
