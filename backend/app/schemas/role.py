from typing import Optional
from pydantic import BaseModel


class FunctionItem(BaseModel):
    function_id: int
    function_name: str

    model_config = {"from_attributes": True}


class RoleUserItem(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class RoleItem(BaseModel):
    id: int
    name: str
    users: list[RoleUserItem] = []
    functions: list[FunctionItem] = []

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str
    user_ids: Optional[list[int]] = None
    function_ids: Optional[list[int]] = None


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    user_ids: Optional[list[int]] = None
    function_ids: Optional[list[int]] = None


class FunctionOptionItem(BaseModel):
    function_id: int
    function_name: str

    model_config = {"from_attributes": True}
