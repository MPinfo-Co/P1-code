"""
Tests for fn_ai_partner_tool APIs — write_custom_table / read_custom_table 工具類型
對應 TDD #13 測試案例 T35-T46
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


def _make_function_folder(db: Session, name: str = "AI夥伴", sort_order: int = 1) -> int:
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


def _setup_admin_with_fn_tool(engine):
    """Create admin user with fn_ai_partner_tool permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_function_folder(db, "AI夥伴", 1)
    fn_tool_id = _make_function(db, "fn_ai_partner_tool", folder_id, 5)
    role_id = _make_role(db, "admin_ct_tool")
    user_id = _make_user(db, "admin_ct_tool@test.com", name="Admin CT Tool")
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_tool_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_tool_id


def _create_custom_table(engine, name: str = "測試資料表") -> int:
    """Insert a custom table with one field. Return table id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    table = CustomTable(name=name, description="test table")
    db.add(table)
    db.flush()
    field = CustomTableField(
        table_id=table.id,
        field_name="欄位A",
        field_type="string",
        sort_order=0,
    )
    db.add(field)
    db.commit()
    tid = table.id
    db.close()
    return tid


def _add_write_custom_table_tool(engine, name: str, target_table_id: int) -> int:
    """Insert a write_custom_table tool with config. Return tool id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = Tool(name=name, tool_type="write_custom_table", auth_type="none")
    db.add(tool)
    db.flush()
    db.add(ToolWriteCustomTableConfig(tool_id=tool.id, target_table_id=target_table_id))
    db.commit()
    tid = tool.id
    db.close()
    return tid


def _add_read_custom_table_tool(
    engine, name: str, target_table_id: int, limit: int = 20, scope: str = "self"
) -> int:
    """Insert a read_custom_table tool with config. Return tool id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = Tool(name=name, tool_type="read_custom_table", auth_type="none")
    db.add(tool)
    db.flush()
    db.add(
        ToolReadCustomTableConfig(
            tool_id=tool.id,
            target_table_id=target_table_id,
            limit=limit,
            scope=scope,
        )
    )
    db.commit()
    tid = tool.id
    db.close()
    return tid


# ---------------------------------------------------------------------------
# T35: GET /tool — 查詢含 write_custom_table_config
# ---------------------------------------------------------------------------


def test_list_tools_contains_write_custom_table_config(client, engine):
    """對應 T35"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id = _create_custom_table(engine, "寫入資料表T35")
    _add_write_custom_table_tool(engine, "WriteTableTool", table_id)

    resp = client.get("/tool", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    tool_item = next((t for t in data if t["name"] == "WriteTableTool"), None)
    assert tool_item is not None
    assert tool_item["tool_type"] == "write_custom_table"
    assert tool_item["write_custom_table_config"] is not None
    assert tool_item["write_custom_table_config"]["target_table_id"] == table_id
    assert tool_item["read_custom_table_config"] is None


# ---------------------------------------------------------------------------
# T36: GET /tool — 查詢含 read_custom_table_config
# ---------------------------------------------------------------------------


def test_list_tools_contains_read_custom_table_config(client, engine):
    """對應 T36"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id = _create_custom_table(engine, "讀取資料表T36")
    _add_read_custom_table_tool(engine, "ReadTableTool", table_id, limit=15, scope="all")

    resp = client.get("/tool", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    tool_item = next((t for t in data if t["name"] == "ReadTableTool"), None)
    assert tool_item is not None
    assert tool_item["tool_type"] == "read_custom_table"
    assert tool_item["read_custom_table_config"] is not None
    assert tool_item["read_custom_table_config"]["target_table_id"] == table_id
    assert tool_item["read_custom_table_config"]["limit"] == 15
    assert tool_item["read_custom_table_config"]["scope"] == "all"
    assert tool_item["write_custom_table_config"] is None


# ---------------------------------------------------------------------------
# T37: POST /tool — 新增成功（write_custom_table）
# ---------------------------------------------------------------------------


def test_add_write_custom_table_tool_returns_201(client, engine):
    """對應 T37"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id = _create_custom_table(engine, "寫入資料表T37")

    payload = {
        "name": "WriteToolT37",
        "tool_type": "write_custom_table",
        "description": "寫入工具說明",
        "target_table_id": table_id,
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"

    # Verify DB
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.name == "WriteToolT37").first()
    assert tool is not None
    assert tool.tool_type == "write_custom_table"
    config = (
        db.query(ToolWriteCustomTableConfig)
        .filter(ToolWriteCustomTableConfig.tool_id == tool.id)
        .first()
    )
    assert config is not None
    assert config.target_table_id == table_id
    db.close()


# ---------------------------------------------------------------------------
# T38: POST /tool — 新增失敗，target_table_id 為空（write_custom_table）
# ---------------------------------------------------------------------------


def test_add_write_custom_table_missing_target_table_returns_400(client, engine):
    """對應 T38"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "WriteToolT38",
        "tool_type": "write_custom_table",
        # target_table_id 未傳
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "目標資料表為必填"


# ---------------------------------------------------------------------------
# T39: POST /tool — 新增失敗，target_table_id 不存在（write_custom_table）
# ---------------------------------------------------------------------------


def test_add_write_custom_table_nonexistent_table_returns_400(client, engine):
    """對應 T39"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "WriteToolT39",
        "tool_type": "write_custom_table",
        "target_table_id": 99999,
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "目標資料表不存在"


# ---------------------------------------------------------------------------
# T40: POST /tool — 新增成功（read_custom_table）
# ---------------------------------------------------------------------------


def test_add_read_custom_table_tool_returns_201(client, engine):
    """對應 T40"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id = _create_custom_table(engine, "讀取資料表T40")

    payload = {
        "name": "ReadToolT40",
        "tool_type": "read_custom_table",
        "target_table_id": table_id,
        "limit": 10,
        "scope": "self",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"

    # Verify DB
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.name == "ReadToolT40").first()
    assert tool is not None
    assert tool.tool_type == "read_custom_table"
    config = (
        db.query(ToolReadCustomTableConfig)
        .filter(ToolReadCustomTableConfig.tool_id == tool.id)
        .first()
    )
    assert config is not None
    assert config.limit == 10
    assert config.scope == "self"
    db.close()


def test_add_read_custom_table_tool_default_limit(client, engine):
    """對應 T40 — limit 未傳入時預設 20"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id = _create_custom_table(engine, "讀取資料表T40default")

    payload = {
        "name": "ReadToolT40Default",
        "tool_type": "read_custom_table",
        "target_table_id": table_id,
        # limit 未傳
        "scope": "all",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.name == "ReadToolT40Default").first()
    config = (
        db.query(ToolReadCustomTableConfig)
        .filter(ToolReadCustomTableConfig.tool_id == tool.id)
        .first()
    )
    assert config.limit == 20  # default
    db.close()


# ---------------------------------------------------------------------------
# T41: POST /tool — 新增失敗，target_table_id 為空（read_custom_table）
# ---------------------------------------------------------------------------


def test_add_read_custom_table_missing_target_table_returns_400(client, engine):
    """對應 T41"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "ReadToolT41",
        "tool_type": "read_custom_table",
        # target_table_id 未傳
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "目標資料表為必填"


# ---------------------------------------------------------------------------
# T42: POST /tool — 新增失敗，scope 不合法（read_custom_table）
# ---------------------------------------------------------------------------


def test_add_read_custom_table_invalid_scope_returns_400(client, engine):
    """對應 T42"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id = _create_custom_table(engine, "讀取資料表T42")

    payload = {
        "name": "ReadToolT42",
        "tool_type": "read_custom_table",
        "target_table_id": table_id,
        "scope": "invalid_value",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "資料範圍值不合法"


# ---------------------------------------------------------------------------
# T43: PATCH /tool/{id} — 修改成功（write_custom_table）
# ---------------------------------------------------------------------------


def test_update_write_custom_table_tool_returns_200(client, engine):
    """對應 T43"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id1 = _create_custom_table(engine, "原始資料表T43")
    table_id2 = _create_custom_table(engine, "新資料表T43")
    tool_id = _add_write_custom_table_tool(engine, "WriteToolT43", table_id1)

    patch_payload = {
        "name": "WriteToolT43",
        "description": "更新說明",
        "target_table_id": table_id2,
    }
    resp = client.patch(f"/tool/{tool_id}", json=patch_payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    config = (
        db.query(ToolWriteCustomTableConfig)
        .filter(ToolWriteCustomTableConfig.tool_id == tool_id)
        .first()
    )
    assert config is not None
    assert config.target_table_id == table_id2
    db.close()


# ---------------------------------------------------------------------------
# T44: PATCH /tool/{id} — 修改成功（read_custom_table）
# ---------------------------------------------------------------------------


def test_update_read_custom_table_tool_returns_200(client, engine):
    """對應 T44"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id = _create_custom_table(engine, "讀取資料表T44")
    tool_id = _add_read_custom_table_tool(engine, "ReadToolT44", table_id, limit=20, scope="self")

    patch_payload = {
        "name": "ReadToolT44",
        "target_table_id": table_id,
        "limit": 5,
        "scope": "all",
    }
    resp = client.patch(f"/tool/{tool_id}", json=patch_payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    config = (
        db.query(ToolReadCustomTableConfig)
        .filter(ToolReadCustomTableConfig.tool_id == tool_id)
        .first()
    )
    assert config is not None
    assert config.limit == 5
    assert config.scope == "all"
    db.close()


# ---------------------------------------------------------------------------
# T44-F1: PATCH — 修改失敗，target_table_id 不存在（write_custom_table）
# ---------------------------------------------------------------------------


def test_update_write_custom_table_nonexistent_table_returns_400(client, engine):
    """對應 T44-F1"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id = _create_custom_table(engine, "資料表T44F1")
    tool_id = _add_write_custom_table_tool(engine, "WriteToolT44F1", table_id)

    patch_payload = {
        "name": "WriteToolT44F1",
        "target_table_id": 99999,
    }
    resp = client.patch(f"/tool/{tool_id}", json=patch_payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "目標資料表不存在"


# ---------------------------------------------------------------------------
# T44-F2: PATCH — 修改失敗，scope 不合法（read_custom_table）
# ---------------------------------------------------------------------------


def test_update_read_custom_table_invalid_scope_returns_400(client, engine):
    """對應 T44-F2"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id = _create_custom_table(engine, "資料表T44F2")
    tool_id = _add_read_custom_table_tool(engine, "ReadToolT44F2", table_id)

    patch_payload = {
        "name": "ReadToolT44F2",
        "target_table_id": table_id,
        "scope": "invalid_value",
    }
    resp = client.patch(f"/tool/{tool_id}", json=patch_payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "資料範圍值不合法"


# ---------------------------------------------------------------------------
# T45: DELETE /tool/{id} — 刪除成功（write_custom_table，清除 config）
# ---------------------------------------------------------------------------


def test_delete_write_custom_table_tool_clears_config(client, engine):
    """對應 T45"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id = _create_custom_table(engine, "資料表T45")
    tool_id = _add_write_custom_table_tool(engine, "WriteToolT45", table_id)

    resp = client.delete(f"/tool/{tool_id}", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    assert db.query(Tool).filter(Tool.id == tool_id).first() is None
    assert (
        db.query(ToolWriteCustomTableConfig)
        .filter(ToolWriteCustomTableConfig.tool_id == tool_id)
        .count()
        == 0
    )
    db.close()


# ---------------------------------------------------------------------------
# T46: DELETE /tool/{id} — 刪除成功（read_custom_table，清除 config）
# ---------------------------------------------------------------------------


def test_delete_read_custom_table_tool_clears_config(client, engine):
    """對應 T46"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    table_id = _create_custom_table(engine, "資料表T46")
    tool_id = _add_read_custom_table_tool(engine, "ReadToolT46", table_id)

    resp = client.delete(f"/tool/{tool_id}", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    assert db.query(Tool).filter(Tool.id == tool_id).first() is None
    assert (
        db.query(ToolReadCustomTableConfig)
        .filter(ToolReadCustomTableConfig.tool_id == tool_id)
        .count()
        == 0
    )
    db.close()


def test_delete_write_custom_table_tool_not_found_returns_404(client, engine):
    """對應 T12-F1 — DELETE /tool/99999 → 404"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    resp = client.delete("/tool/99999", headers=_auth_headers(admin_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "工具不存在"
