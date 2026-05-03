from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.db.models.user import Function, User
from app.schemas.role import FunctionOptionItem

router = APIRouter(prefix="/api/functions", tags=["functions"])


@router.get("/options", status_code=200)
def get_function_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得功能選項清單"""
    functions = db.query(Function).order_by(Function.function_id.asc()).all()
    data = [
        FunctionOptionItem(function_id=f.function_id, function_name=f.function_name)
        for f in functions
    ]
    return {"message": "查詢成功", "data": data}
