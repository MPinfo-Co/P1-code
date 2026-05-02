"""/api/settings router — list, update system params, and get param-type options."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.schema.setting import (
    ParamTypeOptionsResponse,
    SystemParamItem,
    SystemParamListResponse,
    SystemParamUpdate,
    SystemParamUpdateResponse,
)
from app.db.connector import get_db
from app.db.models.fn_setting import SystemParam
from app.db.models.fn_user_role import Role, UserRole
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/api/settings", tags=["setting"])


def _has_setting_permission(user_id: int, db: Session) -> bool:
    """回傳使用者是否具備 fn_setting 功能權限（can_manage_settings）。"""
    return (
        db.query(Role)
        .join(UserRole, Role.id == UserRole.role_id)
        .filter(UserRole.user_id == user_id, Role.can_manage_settings.is_(True))
        .first()
        is not None
    )


@router.get("/options/param-types", response_model=ParamTypeOptionsResponse)
def list_param_type_options(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> ParamTypeOptionsResponse:
    """回傳所有不重複的參數類型清單，依字母升冪排序。"""
    if not _has_setting_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    rows = (
        db.query(SystemParam.param_type)
        .distinct()
        .order_by(SystemParam.param_type.asc())
        .all()
    )
    return ParamTypeOptionsResponse(data=[r.param_type for r in rows])


@router.get("", response_model=SystemParamListResponse)
def list_settings(
    param_type: str | None = Query(None, description="依參數類型過濾，未傳入或空字串時回傳全部。"),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> SystemParamListResponse:
    """查詢系統參數清單，可依參數類型過濾。"""
    if not _has_setting_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    query = db.query(SystemParam)
    if param_type and param_type.strip():
        query = query.filter(SystemParam.param_type == param_type)
    rows = query.order_by(SystemParam.id.asc()).all()

    items = [
        SystemParamItem(
            param_type=r.param_type,
            param_code=r.param_code,
            param_value=r.param_value,
        )
        for r in rows
    ]
    return SystemParamListResponse(data=items)


@router.patch("/{param_code}", response_model=SystemParamUpdateResponse)
def update_setting(
    param_code: str,
    payload: SystemParamUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> SystemParamUpdateResponse:
    """更新指定參數代碼的參數值，限具備管理員（can_manage_settings）角色。"""
    if not _has_setting_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    if not payload.param_value or not payload.param_value.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="參數值不可為空",
        )

    param = db.query(SystemParam).filter(SystemParam.param_code == param_code).first()
    if param is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="參數不存在",
        )

    param.param_value = payload.param_value
    param.updated_by = auth.user_id
    db.commit()
    return SystemParamUpdateResponse()
