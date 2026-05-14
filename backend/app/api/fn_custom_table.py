"""/custom_table router — 自訂資料表管理 (fn_custom_table)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.schema.fn_custom_table import (
    CustomTableCreate,
    CustomTableFieldItem,
    CustomTableItem,
    CustomTableOptionItem,
    CustomTableRecordItem,
    CustomTableRecordsOut,
    CustomTableUpdate,
)
from app.db.connector import get_db
from app.db.models.fn_custom_table import (
    CustomTable,
    CustomTableField,
    CustomTableRecord,
)
from app.db.models.fn_ai_partner_tool import (
    ToolReadCustomTableConfig,
    ToolWriteCustomTableConfig,
)
from app.db.models.function_access import FunctionItems, RoleFunction
from app.db.models.user_role import UserRole
from app.logger_utils import get_system_logger
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/custom_table", tags=["fn_custom_table"])
system_logger = get_system_logger()

FN_CUSTOM_TABLE_NAME = "fn_custom_table"
VALID_FIELD_TYPES = {"string", "number"}


# ---------------------------------------------------------------------------
# Permission helper
# ---------------------------------------------------------------------------


def _has_fn_custom_table_permission(user_id: int, db: Session) -> bool:
    """Return True if the user has fn_custom_table function permission."""
    fn = (
        db.query(FunctionItems)
        .filter(FunctionItems.function_code == FN_CUSTOM_TABLE_NAME)
        .first()
    )
    if fn is None:
        return False
    return (
        db.query(RoleFunction)
        .join(UserRole, RoleFunction.role_id == UserRole.role_id)
        .filter(
            UserRole.user_id == user_id,
            RoleFunction.function_id == fn.function_id,
        )
        .first()
        is not None
    )


def _is_table_referenced_by_tool(table_id: int, db: Session) -> bool:
    """Return True if any write or read custom table tool config references this table."""
    write_ref = (
        db.query(ToolWriteCustomTableConfig)
        .filter(ToolWriteCustomTableConfig.target_table_id == table_id)
        .first()
    )
    if write_ref:
        return True
    read_ref = (
        db.query(ToolReadCustomTableConfig)
        .filter(ToolReadCustomTableConfig.target_table_id == table_id)
        .first()
    )
    return read_ref is not None


# ---------------------------------------------------------------------------
# GET /custom_table/options
# ---------------------------------------------------------------------------


@router.get("/options", status_code=status.HTTP_200_OK)
def list_custom_table_options(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Return all custom tables as options. Requires login only."""
    tables = db.query(CustomTable).order_by(CustomTable.created_at.asc()).all()

    table_ids = [t.id for t in tables]
    all_fields = (
        db.query(CustomTableField)
        .filter(CustomTableField.table_id.in_(table_ids))
        .order_by(CustomTableField.table_id, CustomTableField.sort_order)
        .all()
        if table_ids
        else []
    )
    fields_by_table: dict[int, list] = {}
    for f in all_fields:
        fields_by_table.setdefault(f.table_id, []).append(f)

    data = []
    for t in tables:
        fields = fields_by_table.get(t.id, [])
        item = CustomTableOptionItem(
            id=t.id,
            name=t.name,
            fields=[
                {"field_name": f.field_name, "field_type": f.field_type} for f in fields
            ],
        )
        data.append(item.model_dump())

    return {"message": "查詢成功", "data": data}


# ---------------------------------------------------------------------------
# GET /custom_table
# ---------------------------------------------------------------------------


@router.get("", status_code=status.HTTP_200_OK)
def list_custom_tables(
    keyword: str | None = Query(None, description="表格名稱關鍵字篩選（ILIKE）"),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """List custom tables. Requires fn_custom_table permission."""
    if not _has_fn_custom_table_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    query = db.query(CustomTable)
    if keyword:
        query = query.filter(CustomTable.name.ilike(f"%{keyword}%"))
    tables = query.order_by(CustomTable.created_at.asc()).all()

    table_ids = [t.id for t in tables]
    # Count fields per table
    field_counts_rows = (
        db.query(CustomTableField.table_id, func.count(CustomTableField.id))
        .filter(CustomTableField.table_id.in_(table_ids))
        .group_by(CustomTableField.table_id)
        .all()
        if table_ids
        else []
    )
    field_counts: dict[int, int] = {row[0]: row[1] for row in field_counts_rows}

    # Count records per table
    record_counts_rows = (
        db.query(CustomTableRecord.table_id, func.count(CustomTableRecord.id))
        .filter(CustomTableRecord.table_id.in_(table_ids))
        .group_by(CustomTableRecord.table_id)
        .all()
        if table_ids
        else []
    )
    record_counts: dict[int, int] = {row[0]: row[1] for row in record_counts_rows}

    # Check tool references for all tables
    referenced_write = set(
        row[0]
        for row in db.query(ToolWriteCustomTableConfig.target_table_id)
        .filter(ToolWriteCustomTableConfig.target_table_id.in_(table_ids))
        .distinct()
        .all()
    ) if table_ids else set()

    referenced_read = set(
        row[0]
        for row in db.query(ToolReadCustomTableConfig.target_table_id)
        .filter(ToolReadCustomTableConfig.target_table_id.in_(table_ids))
        .distinct()
        .all()
    ) if table_ids else set()

    referenced_ids = referenced_write | referenced_read

    data = []
    for t in tables:
        item = CustomTableItem(
            id=t.id,
            name=t.name,
            description=t.description,
            field_count=field_counts.get(t.id, 0),
            record_count=record_counts.get(t.id, 0),
            is_tool_referenced=t.id in referenced_ids,
        )
        data.append(item.model_dump())

    return {"message": "查詢成功", "data": data}


# ---------------------------------------------------------------------------
# POST /custom_table
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
def add_custom_table(
    payload: CustomTableCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Create a new custom table. Requires fn_custom_table permission."""
    if not _has_fn_custom_table_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    # Validate name
    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="表格名稱為必填"
        )
    if db.query(CustomTable).filter(CustomTable.name == payload.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="表格名稱已存在"
        )

    # Validate fields
    if not payload.fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="至少須定義一個欄位"
        )
    for field in payload.fields:
        if not field.field_name or not field.field_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="欄位名稱不可為空"
            )
        if field.field_type not in VALID_FIELD_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="欄位型別不合法"
            )

    # Create table
    table = CustomTable(name=payload.name, description=payload.description)
    db.add(table)
    db.flush()

    # Create fields
    for idx, field in enumerate(payload.fields):
        db.add(
            CustomTableField(
                table_id=table.id,
                field_name=field.field_name,
                field_type=field.field_type,
                description=field.description,
                sort_order=idx,
            )
        )

    db.commit()
    system_logger.info(
        f"User {auth.user_id} created custom table {table.id} ({table.name})"
    )
    return {"message": "新增成功"}


# ---------------------------------------------------------------------------
# PATCH /custom_table/{id}
# ---------------------------------------------------------------------------


@router.patch("/{table_id}", status_code=status.HTTP_200_OK)
def update_custom_table(
    table_id: int,
    payload: CustomTableUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Update a custom table. Requires fn_custom_table permission."""
    if not _has_fn_custom_table_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    table = db.query(CustomTable).filter(CustomTable.id == table_id).first()
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="資料表不存在"
        )

    # Validate name
    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="表格名稱為必填"
        )
    conflict = (
        db.query(CustomTable)
        .filter(CustomTable.name == payload.name, CustomTable.id != table_id)
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="表格名稱已存在"
        )

    # Validate fields
    if not payload.fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="至少須定義一個欄位"
        )
    for field in payload.fields:
        if not field.field_name or not field.field_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="欄位名稱不可為空"
            )
        if field.field_type not in VALID_FIELD_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="欄位型別不合法"
            )

    # Check if this table has records
    has_records = (
        db.query(CustomTableRecord)
        .filter(CustomTableRecord.table_id == table_id)
        .first()
        is not None
    )

    if has_records:
        # Get existing field names
        existing_fields = (
            db.query(CustomTableField)
            .filter(CustomTableField.table_id == table_id)
            .all()
        )
        existing_field_names = {f.field_name for f in existing_fields}
        new_field_names = {f.field_name for f in payload.fields}

        # Check if any existing field is being removed
        removed = existing_field_names - new_field_names
        if removed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已有資料的欄位不可刪除",
            )

    # Update table
    table.name = payload.name
    table.description = payload.description

    # Replace fields
    db.query(CustomTableField).filter(CustomTableField.table_id == table_id).delete()
    for idx, field in enumerate(payload.fields):
        db.add(
            CustomTableField(
                table_id=table.id,
                field_name=field.field_name,
                field_type=field.field_type,
                description=field.description,
                sort_order=idx,
            )
        )

    db.commit()
    system_logger.info(
        f"User {auth.user_id} updated custom table {table.id} ({table.name})"
    )
    return {"message": "更新成功"}


# ---------------------------------------------------------------------------
# DELETE /custom_table/{id}
# ---------------------------------------------------------------------------


@router.delete("/{table_id}", status_code=status.HTTP_200_OK)
def delete_custom_table(
    table_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Delete a custom table. Requires fn_custom_table permission.

    TDD #8：刪除前檢查是否已被工具引用。
    """
    if not _has_fn_custom_table_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    table = db.query(CustomTable).filter(CustomTable.id == table_id).first()
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="資料表不存在"
        )

    # Check tool references before deletion
    if _is_table_referenced_by_tool(table_id, db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此資料表已被 AI 工具引用，請先移除相關工具的引用後再刪除",
        )

    # Delete records, fields, then table
    db.query(CustomTableRecord).filter(CustomTableRecord.table_id == table_id).delete()
    db.query(CustomTableField).filter(CustomTableField.table_id == table_id).delete()
    db.delete(table)
    db.commit()
    system_logger.info(f"User {auth.user_id} deleted custom table {table_id}")
    return {"message": "刪除成功"}


# ── GET /custom_table/{table_id}/records ─────────────────────────────────────


@router.get(
    "/{table_id}/records",
    response_model=CustomTableRecordsOut,
    status_code=status.HTTP_200_OK,
)
def list_records(
    table_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> CustomTableRecordsOut:
    """List all records for a custom table."""
    if not _has_fn_custom_table_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )
    table = db.query(CustomTable).filter(CustomTable.id == table_id).first()
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="資料表不存在"
        )
    fields = (
        db.query(CustomTableField)
        .filter(CustomTableField.table_id == table_id)
        .order_by(CustomTableField.sort_order.asc())
        .all()
    )
    records = (
        db.query(CustomTableRecord)
        .filter(CustomTableRecord.table_id == table_id)
        .order_by(CustomTableRecord.updated_at.desc())
        .all()
    )
    return CustomTableRecordsOut(
        fields=[CustomTableFieldItem.model_validate(f) for f in fields],
        records=[CustomTableRecordItem.model_validate(r) for r in records],
    )


# ── DELETE /custom_table/{table_id}/records/{record_id} ──────────────────────


@router.delete("/{table_id}/records/{record_id}", status_code=status.HTTP_200_OK)
def delete_record(
    table_id: int,
    record_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Delete a single record."""
    if not _has_fn_custom_table_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )
    table = db.query(CustomTable).filter(CustomTable.id == table_id).first()
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="資料表不存在"
        )
    record = (
        db.query(CustomTableRecord)
        .filter(
            CustomTableRecord.id == record_id,
            CustomTableRecord.table_id == table_id,
        )
        .first()
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="記錄不存在"
        )
    db.delete(record)
    db.commit()
    return {"message": "刪除成功"}


# ── DELETE /custom_table/{table_id}/records ───────────────────────────────────


@router.delete("/{table_id}/records", status_code=status.HTTP_200_OK)
def delete_all_records(
    table_id: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> dict:
    """Delete all records for a custom table."""
    if not _has_fn_custom_table_permission(auth.user_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )
    table = db.query(CustomTable).filter(CustomTable.id == table_id).first()
    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="資料表不存在"
        )
    db.query(CustomTableRecord).filter(CustomTableRecord.table_id == table_id).delete()
    db.commit()
    return {"message": "刪除成功"}
