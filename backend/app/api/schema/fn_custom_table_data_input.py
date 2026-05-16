"""Pydantic schemas for /custom_table_data_input endpoints."""

from datetime import datetime

from pydantic import BaseModel


class AuthorizedTableItem(BaseModel):
    """Single authorized custom table item."""

    id: int
    name: str
    description: str | None = None


class AuthorizedTableListOut(BaseModel):
    """Response for GET /custom_table_data_input/tables."""

    message: str = "查詢成功"
    data: list[AuthorizedTableItem]


class TableFieldItem(BaseModel):
    """Single field definition within a custom table."""

    id: int
    field_name: str
    field_type: str
    sort_order: int


class TableRecordItem(BaseModel):
    """Single record row within a custom table."""

    id: int
    data: dict
    updated_at: datetime
    updated_by_name: str | None = None


class TableRecordsData(BaseModel):
    """Payload for records list response."""

    fields: list[TableFieldItem]
    records: list[TableRecordItem]
    total: int = 0
    exceeded: bool = False


class TableRecordsOut(BaseModel):
    """Response for GET /custom_table_data_input/tables/{id}/records."""

    message: str = "查詢成功"
    data: TableRecordsData


class RecordAddRequest(BaseModel):
    """Body for POST /custom_table_data_input/tables/{id}/records."""

    data: dict


class RecordAddOut(BaseModel):
    """Response for POST /custom_table_data_input/tables/{id}/records (201)."""

    message: str = "新增成功"


class RecordUpdateRequest(BaseModel):
    """Body for PATCH /custom_table_data_input/tables/{id}/records/{record_id}."""

    data: dict


class RecordUpdateOut(BaseModel):
    """Response for PATCH /custom_table_data_input/tables/{id}/records/{record_id} (200)."""

    message: str = "更新成功"


class RecordDelOut(BaseModel):
    """Response for DELETE /custom_table_data_input/tables/{id}/records/{record_id} (200)."""

    message: str = "刪除成功"


class ImportOut(BaseModel):
    """Response for POST /custom_table_data_input/tables/{id}/import (200)."""

    message: str = "匯入成功"


class TableOptionItem(BaseModel):
    """Single item in the custom table options list."""

    id: int
    name: str


class TableOptionsOut(BaseModel):
    """Response for GET /custom_table_data_input/options."""

    message: str = "查詢成功"
    data: list[TableOptionItem]
