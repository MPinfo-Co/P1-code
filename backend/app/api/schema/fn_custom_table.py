"""Pydantic schemas for fn_custom_table API."""

from datetime import datetime

from pydantic import BaseModel, Field


class CustomTableFieldCreate(BaseModel):
    """單筆欄位定義輸入。"""

    field_name: str = Field(..., description="欄位名稱")
    field_type: str = Field(..., description="欄位型別：string / number")
    description: str | None = Field(None, description="欄位說明")


class CustomTableCreate(BaseModel):
    """新增自訂資料表輸入。"""

    name: str = Field(..., description="表格名稱")
    description: str | None = Field(None, description="表格用途說明")
    fields: list[CustomTableFieldCreate] = Field(
        ..., description="欄位清單（至少一筆）"
    )


class CustomTableUpdate(BaseModel):
    """修改自訂資料表輸入。"""

    name: str = Field(..., description="表格名稱")
    description: str | None = Field(None, description="表格用途說明")
    fields: list[CustomTableFieldCreate] = Field(
        ..., description="欄位清單（至少一筆）"
    )


class CustomTableFieldItem(BaseModel):
    """單筆欄位定義輸出。"""

    model_config = {"from_attributes": True}

    id: int
    field_name: str
    field_type: str
    description: str | None
    sort_order: int


class CustomTableItem(BaseModel):
    """自訂資料表清單單項輸出。"""

    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
    field_count: int
    record_count: int
    is_tool_referenced: bool = False


class CustomTableOptionFieldItem(BaseModel):
    """選單中欄位清單單項輸出。"""

    field_name: str
    field_type: str


class CustomTableOptionItem(BaseModel):
    """自訂資料表選單單項輸出。"""

    id: int
    name: str
    fields: list[CustomTableOptionFieldItem]


class CustomTableDetailOut(BaseModel):
    """單一資料表詳細輸出（含欄位清單）。"""

    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
    has_records: bool
    fields: list[CustomTableFieldItem]


class CustomTableRecordItem(BaseModel):
    """單筆 record 輸出。"""

    model_config = {"from_attributes": True}

    id: int
    data: dict
    updated_by: int
    updated_at: datetime


class CustomTableRecordsOut(BaseModel):
    """資料查看頁輸出：欄位定義 + records 清單。"""

    table_name: str
    fields: list[CustomTableFieldItem]
    records: list[CustomTableRecordItem]


# ── Relations schemas ──────────────────────────────────────────────────────────


class CustomTableRelationItem(BaseModel):
    """單筆關聯資料輸出。"""

    model_config = {"from_attributes": True}

    id: int
    src_table_id: int
    src_field: str
    dst_table_id: int
    dst_field: str


class CustomTableRelationInput(BaseModel):
    """儲存關聯輸入的單筆關聯物件。"""

    src_table_id: int = Field(..., description="來源資料表 id")
    src_field: str = Field(..., description="來源欄位名稱")
    dst_table_id: int = Field(..., description="目標資料表 id")
    dst_field: str = Field(..., description="目標欄位名稱")


class CustomTableRelationsSaveRequest(BaseModel):
    """PUT /custom_table/relations 請求 body。"""

    relations: list[CustomTableRelationInput] = Field(
        ..., description="關聯清單（空陣列表示清除全部）"
    )
