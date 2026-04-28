from pydantic import BaseModel


class EchoResponse(BaseModel):
    message: str
    data: str
