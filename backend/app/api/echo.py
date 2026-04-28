from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/echo", tags=["echo"])


@router.get("")
def get_echo(message: str = Query(..., description="回傳訊息內容")):
    return {"message": "ok", "data": {"message": message}}
