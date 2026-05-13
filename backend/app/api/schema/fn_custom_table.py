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


class CustomTableOptionFieldItem(BaseModel):
    """選單中欄位清單單項輸出。"""

    field_name: str
    field_type: str


class CustomTableOptionItem(BaseModel):
    """自訂資料表選單單項輸出。"""

    id: int
    name: str
    fields: list[CustomTableOptionFieldItem]


class CustomTableRecordItem(BaseModel):
    """單筆 record 輸出。"""

    model_config = {"from_attributes": True}

    id: int
    data: dict
    created_at: datetime


class CustomTableRecordsOut(BaseModel):
    """資料查看頁輸出：欄位定義 + records 清單。"""

    fields: list[CustomTableFieldItem]
    records: list[CustomTableRecordItem]
