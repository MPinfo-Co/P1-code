from fastapi import APIRouter, Query
from app.schemas.echo import EchoResponse

router = APIRouter(prefix="/api")


@router.get("/echo", response_model=EchoResponse)
def echo_message(message: str = Query(..., description="要回傳的訊息")):
    return EchoResponse(message="ok", data=message)
