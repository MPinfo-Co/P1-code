from pydantic import BaseModel


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
