"""
Tests for fn_custom_table APIs — 刪除保護與 is_tool_referenced 查詢
對應 TDD #14 測試案例 T24-T27
"""

import os

from sqlalchemy.orm import Session, sessionmaker

from app.db.models.fn_custom_table import CustomTable, CustomTableField
from app.db.models.fn_ai_partner_tool import (
    Tool,
    ToolReadCustomTableConfig,
    ToolWriteCustomTableConfig,
)
from app.db.models.function_access import (
    FunctionItems as Function,
    FunctionFolder,
    RoleFunction,
)
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password

os.environ.setdefault("AES_KEY", "test-aes-256-key-for-pytest-12345")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_function_folder(
    db: Session, name: str = "自訂資料表", sort_order: int = 1
) -> int:
    folder = FunctionFolder(folder_code=name, folder_label=name, sort_order=sort_order)
    db.add(folder)
    db.flush()
    return folder.id


def _make_function(db: Session, name: str, folder_id: int, sort_order: int = 1) -> int:
    fn = Function(
        function_code=name,
        function_label=name,
        folder_id=folder_id,
        sort_order=sort_order,
    )
    db.add(fn)
    db.flush()
    return fn.function_id


def _make_role(db: Session, name: str) -> int:
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role.id


def _make_user(db: Session, email: str, name: str = "Test User") -> int:
    user = User(name=name, email=email, password_hash=hash_password("password123"))
    db.add(user)
    db.flush()
    return user.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _grant_function(db: Session, role_id: int, function_id: int) -> None:
    db.add(RoleFunction(role_id=role_id, function_id=function_id))
    db.flush()


def _auth_headers(user_id: int) -> dict:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _setup_admin_with_fn_custom_table(engine):
    """Create admin user with fn_custom_table function permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_function_folder(db, "自訂資料表", 1)
    fn_id = _make_function(db, "fn_custom_table", folder_id, 5)
    role_id = _make_role(db, "admin_ct_del")
    user_id = _make_user(db, "admin_ct_del@test.com", name="Admin CT Del")
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_id


def _create_custom_table(engine, name: str) -> int:
    """Insert a custom table with one field. Return table id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    table = CustomTable(name=name, description="test table")
    db.add(table)
    db.flush()
    db.add(
        CustomTableField(
            table_id=table.id,
            field_name="欄位A",
            field_type="string",
            sort_order=0,
        )
    )
    db.commit()
    tid = table.id
    db.close()
    return tid


def _create_write_tool_referencing(engine, table_id: int, tool_name: str) -> int:
    """Insert a write_custom_table tool config that references the given table. Return tool id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = Tool(name=tool_name, tool_type="write_custom_table", auth_type="none")
    db.add(tool)
    db.flush()
    db.add(ToolWriteCustomTableConfig(tool_id=tool.id, target_table_id=table_id))
    db.commit()
    tid = tool.id
    db.close()
    return tid


def _create_read_tool_referencing(engine, table_id: int, tool_name: str) -> int:
    """Insert a read_custom_table tool config that references the given table. Return tool id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = Tool(name=tool_name, tool_type="read_custom_table", auth_type="none")
    db.add(tool)
    db.flush()
    db.add(
        ToolReadCustomTableConfig(
            tool_id=tool.id,
            target_table_id=table_id,
            limit=20,
            scope="self",
        )
    )
    db.commit()
    tid = tool.id
    db.close()
    return tid


# ---------------------------------------------------------------------------
# T24: DELETE /custom_table/{id} — 刪除失敗，已被 write_custom_table 工具引用
# ---------------------------------------------------------------------------


def test_delete_table_referenced_by_write_tool_returns_400(client, engine):
    """對應 T24"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _create_custom_table(engine, "被寫入工具引用T24")
    _create_write_tool_referencing(engine, table_id, "WriteRefToolT24")

    resp = client.delete(f"/custom_table/{table_id}", headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert (
        resp.json()["detail"]
        == "此資料表已被 AI 工具引用，請先移除相關工具的引用後再刪除"
    )

    # Table should still exist in DB
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    assert db.query(CustomTable).filter(CustomTable.id == table_id).first() is not None
    db.close()


# ---------------------------------------------------------------------------
# T25: DELETE /custom_table/{id} — 刪除失敗，已被 read_custom_table 工具引用
# ---------------------------------------------------------------------------


def test_delete_table_referenced_by_read_tool_returns_400(client, engine):
    """對應 T25"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _create_custom_table(engine, "被讀取工具引用T25")
    _create_read_tool_referencing(engine, table_id, "ReadRefToolT25")

    resp = client.delete(f"/custom_table/{table_id}", headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert (
        resp.json()["detail"]
        == "此資料表已被 AI 工具引用，請先移除相關工具的引用後再刪除"
    )

    # Table should still exist in DB
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    assert db.query(CustomTable).filter(CustomTable.id == table_id).first() is not None
    db.close()


# ---------------------------------------------------------------------------
# T26: DELETE /custom_table/{id} — 刪除成功（未被任何工具引用）
# ---------------------------------------------------------------------------


def test_delete_table_not_referenced_returns_200(client, engine):
    """對應 T26"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    table_id = _create_custom_table(engine, "未被引用T26")

    resp = client.delete(f"/custom_table/{table_id}", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    # Table, fields should be removed from DB
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    assert db.query(CustomTable).filter(CustomTable.id == table_id).first() is None
    assert (
        db.query(CustomTableField).filter(CustomTableField.table_id == table_id).count()
        == 0
    )
    db.close()


# ---------------------------------------------------------------------------
# T27: GET /custom_table — 查詢回傳 is_tool_referenced
# ---------------------------------------------------------------------------


def test_list_tables_returns_is_tool_referenced(client, engine):
    """對應 T27"""
    admin_id, _, _ = _setup_admin_with_fn_custom_table(engine)
    referenced_id = _create_custom_table(engine, "被引用的資料表T27")
    unreferenced_id = _create_custom_table(engine, "未被引用的資料表T27")

    # Reference the first table via a write_custom_table tool
    _create_write_tool_referencing(engine, referenced_id, "RefToolT27")

    resp = client.get("/custom_table", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]

    referenced_item = next((t for t in data if t["id"] == referenced_id), None)
    unreferenced_item = next((t for t in data if t["id"] == unreferenced_id), None)

    assert referenced_item is not None
    assert unreferenced_item is not None
    assert referenced_item["is_tool_referenced"] is True
    assert unreferenced_item["is_tool_referenced"] is False
