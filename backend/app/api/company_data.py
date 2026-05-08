"""/api/company-data router — CRUD for fn_company_data."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.schema.company_data import (
    CompanyDataCreate,
    CompanyDataItem,
    CompanyDataUpdate,
)
from app.db.connector import get_db
from app.db.models.fn_company_data import CompanyData
from app.db.models.function_access import FunctionItems, RoleFunction
from app.db.models.user_role import UserRole
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/company-data", tags=["company-data"])

FN_COMPANY_DATA = "fn_company_data"


def _has_company_data_permission(user_id: int, db: Session) -> bool:
    """Return True if the user has fn_company_data function permission."""
    fn = (
        db.query(FunctionItems)
        .filter(FunctionItems.function_code == FN_COMPANY_DATA)
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


# ---------------------------------------------------------------------------
# GET /api/company-data
# ---------------------------------------------------------------------------


@router.get("")
def list_company_data(
    keyword: str | None = Query(None, description="關鍵字篩選（name / content）"),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
):
    """查詢公司資料列表，支援 keyword 篩選。需登入且具備 fn_company_data 功能權限。"""
    if not _has_company_data_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    query = db.query(CompanyData)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                CompanyData.name.ilike(pattern),
                CompanyData.content.ilike(pattern),
            )
        )
    rows = query.order_by(CompanyData.created_at.asc()).all()

    result = [
        CompanyDataItem(id=row.id, name=row.name, content=row.content) for row in rows
    ]
    return {"message": "查詢成功", "data": [i.model_dump() for i in result]}


# ---------------------------------------------------------------------------
# POST /api/company-data
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
def create_company_data(
    payload: CompanyDataCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
):
    """新增公司資料。需登入且具備 fn_company_data 功能權限。"""
    if not _has_company_data_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="資料名稱不可為空",
        )
    if len(payload.name.strip()) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="資料名稱不可超過 200 字",
        )

    if db.query(CompanyData).filter(CompanyData.name == payload.name).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="資料名稱已存在",
        )

    if not payload.content or not payload.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="內容不可為空",
        )

    record = CompanyData(name=payload.name, content=payload.content)
    db.add(record)
    db.commit()
    return {"message": "新增成功"}


# ---------------------------------------------------------------------------
# PATCH /api/company-data/{id}
# ---------------------------------------------------------------------------


@router.patch("/{record_id}")
def update_company_data(
    record_id: int,
    payload: CompanyDataUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
):
    """更新公司資料。需登入且具備 fn_company_data 功能權限。"""
    if not _has_company_data_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    record = db.get(CompanyData, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="資料不存在",
        )

    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="資料名稱不可為空",
        )
    if len(payload.name.strip()) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="資料名稱不可超過 200 字",
        )

    conflict = (
        db.query(CompanyData)
        .filter(CompanyData.name == payload.name, CompanyData.id != record_id)
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="資料名稱已存在",
        )

    if not payload.content or not payload.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="內容不可為空",
        )

    record.name = payload.name
    record.content = payload.content

    db.commit()
    return {"message": "更新成功"}


# ---------------------------------------------------------------------------
# DELETE /api/company-data/{id}
# ---------------------------------------------------------------------------


@router.delete("/{record_id}")
def delete_company_data(
    record_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
):
    """刪除公司資料。需登入且具備 fn_company_data 功能權限。"""
    if not _has_company_data_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    record = db.get(CompanyData, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="資料不存在",
        )

    db.delete(record)
    db.commit()
    return {"message": "刪除成功"}
