"""/api/navigation router — returns full navigation structure."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.connector import get_db
from app.db.models.function_access import FunctionItems, FunctionFolder
from app.utils.util_store import AuthContext, authenticate
from app.api.schema.navigation import NavFolderItem, NavFunctionItem, NavigationOut

router = APIRouter(prefix="/navigation", tags=["navigation"])


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
            db.query(FunctionItems)
            .filter(FunctionItems.folder_id == folder.id)
            .order_by(FunctionItems.sort_order.asc())
            .all()
        )
        result.append(
            NavFolderItem(
                folder_code=folder.folder_code,
                folder_label=folder.folder_label,
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
