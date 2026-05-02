"""/api/navigation router — returns full navigation structure."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.connector import get_db
from app.db.models.fn_navbar import Function, FunctionFolder
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/api/navigation", tags=["navigation"])


class NavFunctionItem(BaseModel):
    function_code: str
    function_label: str
    sort_order: int


class NavFolderItem(BaseModel):
    folder_code: str
    folder_label: str
    default_open: bool
    sort_order: int
    items: list[NavFunctionItem]


class NavigationOut(BaseModel):
    message: str = "查詢成功"
    data: list[NavFolderItem]


@router.get("", response_model=NavigationOut)
def get_navigation(
    auth: AuthContext = Depends(authenticate),
    db: Session = Depends(get_db),
) -> NavigationOut:
    """Return full navigation structure (all folders + functions), ordered by sort_order."""
    folders = db.query(FunctionFolder).order_by(FunctionFolder.sort_order.asc()).all()
    result = []
    for folder in folders:
        fns = (
            db.query(Function)
            .filter(Function.folder_id == folder.id)
            .order_by(Function.sort_order.asc())
            .all()
        )
        result.append(
            NavFolderItem(
                folder_code=folder.folder_code,
                folder_label=folder.folder_label,
                default_open=folder.default_open,
                sort_order=folder.sort_order,
                items=[
                    NavFunctionItem(
                        function_code=fn.function_code,
                        function_label=fn.function_label,
                        sort_order=fn.sort_order,
                    )
                    for fn in fns
                ],
            )
        )
    return NavigationOut(data=result)
