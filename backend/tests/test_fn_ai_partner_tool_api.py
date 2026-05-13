"""
Tests for fn_ai_partner_tool APIs:
  GET    /tool
  POST   /tool
  PATCH  /tool/{id}
  DELETE /tool/{id}
  POST   /tool/test
"""

import os
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session, sessionmaker

from app.db.models.fn_ai_partner_tool import Tool, ToolBodyParam, ToolImageField
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
    db: Session, name: str = "AI夥伴", sort_order: int = 1
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


def _make_user(
    db: Session, email: str, name: str = "Test User", password: str = "password123"
) -> int:
    user = User(name=name, email=email, password_hash=hash_password(password))
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
    """Create admin user with fn_ai_partner_tool permission. Return (user_id, role_id, fn_tool_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_function_folder(db, "AI夥伴", 1)
    fn_tool_id = _make_function(db, "fn_ai_partner_tool", folder_id, 5)
    role_id = _make_role(db, "admin")
    user_id = _make_user(db, "admin@test.com", name="Admin User")
    _assign_role(db, user_id, role_id)
    _grant_function(db, role_id, fn_tool_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_tool_id


def _setup_plain_user(engine, email: str = "plain@test.com"):
    """Create a user without fn_ai_partner_tool permission. Return (user_id, role_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, "plain_role")
    user_id = _make_user(db, email, name="Plain User")
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id, role_id


def _add_tool(
    engine, name: str, http_method: str = "GET", tool_type: str = "external_api"
) -> int:
    """Insert a tool directly. Return tool id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = Tool(
        name=name,
        tool_type=tool_type,
        endpoint_url="https://example.com/api" if tool_type == "external_api" else None,
        http_method=http_method if tool_type == "external_api" else None,
        auth_type="none",
    )
    db.add(tool)
    db.commit()
    tid = tool.id
    db.close()
    return tid


def _add_image_extract_tool(engine, name: str, image_fields: list | None = None) -> int:
    """Insert an image_extract tool with optional image fields. Return tool id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = Tool(
        name=name,
        tool_type="image_extract",
        endpoint_url=None,
        http_method=None,
        auth_type="none",
    )
    db.add(tool)
    db.flush()
    tid = tool.id
    for idx, field in enumerate(image_fields or []):
        db.add(
            ToolImageField(
                tool_id=tid,
                field_name=field["field_name"],
                field_type=field.get("field_type", "string"),
                description=field.get("description"),
                sort_order=idx,
            )
        )
    db.commit()
    db.close()
    return tid


# ---------------------------------------------------------------------------
# GET /tool — T1, T2, T3
# ---------------------------------------------------------------------------


def test_list_tools_returns_200(client, engine):
    """對應 T1"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    _add_tool(engine, "Slack Notify")
    _add_tool(engine, "Jira Create")

    resp = client.get("/tool", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert isinstance(body["data"], list)
    names = [item["name"] for item in body["data"]]
    assert "Slack Notify" in names
    assert "Jira Create" in names
    # credential_enc must NOT be present in response
    for item in body["data"]:
        assert "credential_enc" not in item
        assert "has_credential" in item


def test_list_tools_keyword_filter(client, engine):
    """對應 T2"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    _add_tool(engine, "Slack Notify")
    _add_tool(engine, "Jira Create")

    resp = client.get("/tool?keyword=Slack", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    names = [item["name"] for item in data]
    assert "Slack Notify" in names
    assert "Jira Create" not in names


def test_list_tools_no_permission_returns_403(client, engine):
    """對應 T3"""
    user_id, _ = _setup_plain_user(engine)

    resp = client.get("/tool", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_list_tools_unauthenticated_returns_401(client, engine):
    """未登入 GET /tool 應回 401"""
    resp = client.get("/tool")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /tool — T4, T5, T6, T7, T8, T9
# ---------------------------------------------------------------------------


def test_add_tool_returns_201(client, engine):
    """對應 T4"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "My Tool",
        "endpoint_url": "https://api.example.com/v1",
        "http_method": "GET",
        "auth_type": "none",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"


def test_add_tool_with_bearer_and_body_params(client, engine):
    """對應 T5"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "Bearer Tool",
        "endpoint_url": "https://api.example.com/v1",
        "http_method": "POST",
        "auth_type": "bearer",
        "credential": "my-secret-token",
        "body_params": [
            {
                "param_name": "message",
                "param_type": "string",
                "is_required": True,
                "description": "The message",
            },
        ],
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"

    # Verify body param was written
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.name == "Bearer Tool").first()
    assert tool is not None
    params = db.query(ToolBodyParam).filter(ToolBodyParam.tool_id == tool.id).all()
    assert len(params) == 1
    assert params[0].param_name == "message"
    db.close()


def test_add_tool_empty_name_returns_400(client, engine):
    """對應 T6"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "",
        "endpoint_url": "https://api.example.com/v1",
        "http_method": "GET",
        "auth_type": "none",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "工具名稱為必填"


def test_add_tool_empty_url_returns_400(client, engine):
    """對應 T7"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "Some Tool",
        "endpoint_url": "",
        "http_method": "GET",
        "auth_type": "none",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "API Endpoint URL 為必填"


def test_add_tool_duplicate_name_returns_400(client, engine):
    """對應 T8"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    _add_tool(engine, "Duplicate Tool")

    payload = {
        "name": "Duplicate Tool",
        "endpoint_url": "https://api.example.com/v1",
        "http_method": "GET",
        "auth_type": "none",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "工具名稱已存在"


def test_add_tool_api_key_missing_header_name_returns_400(client, engine):
    """對應 T9"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "API Key Tool",
        "endpoint_url": "https://api.example.com/v1",
        "http_method": "GET",
        "auth_type": "api_key",
        "credential": "my-api-key",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "API Key 模式下 Header 名稱為必填"


def test_add_tool_no_permission_returns_403(client, engine):
    """未授權 POST /tool 應回 403"""
    user_id, _ = _setup_plain_user(engine)

    payload = {
        "name": "Some Tool",
        "endpoint_url": "https://api.example.com",
        "http_method": "GET",
        "auth_type": "none",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PATCH /tool/{id} — T10, T11, T12
# ---------------------------------------------------------------------------


def test_update_tool_returns_200(client, engine):
    """對應 T10"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    tool_id = _add_tool(engine, "Old Name")

    payload = {
        "name": "New Name",
        "endpoint_url": "https://api.example.com/v2",
        "http_method": "POST",
        "auth_type": "none",
    }
    resp = client.patch(
        f"/tool/{tool_id}", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"


def test_update_tool_empty_credential_keeps_existing(client, engine):
    """對應 T11"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    # Create tool with credential via POST
    post_payload = {
        "name": "Credential Tool",
        "endpoint_url": "https://api.example.com",
        "http_method": "GET",
        "auth_type": "bearer",
        "credential": "original-token",
    }
    client.post("/tool", json=post_payload, headers=_auth_headers(admin_id))

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.name == "Credential Tool").first()
    original_enc = tool.credential_enc
    tool_id = tool.id
    db.close()

    # Update without credential
    patch_payload = {
        "name": "Credential Tool",
        "endpoint_url": "https://api.example.com",
        "http_method": "GET",
        "auth_type": "bearer",
        "credential": "",  # empty — should not change
    }
    resp = client.patch(
        f"/tool/{tool_id}", json=patch_payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200

    db = Session_()
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    assert tool.credential_enc == original_enc  # credential preserved
    db.close()


def test_update_tool_not_found_returns_404(client, engine):
    """對應 T12"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "Whatever",
        "endpoint_url": "https://api.example.com",
        "http_method": "GET",
        "auth_type": "none",
    }
    resp = client.patch("/tool/99999", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "工具不存在"


def test_update_tool_no_permission_returns_403(client, engine):
    """未授權 PATCH /tool/{id} 應回 403"""
    user_id, _ = _setup_plain_user(engine, "plain2@test.com")
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    tool_id = _add_tool(engine, "Protected Tool")

    payload = {
        "name": "Hacked",
        "endpoint_url": "https://api.example.com",
        "http_method": "GET",
        "auth_type": "none",
    }
    resp = client.patch(
        f"/tool/{tool_id}", json=payload, headers=_auth_headers(user_id)
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /tool/{id} — T13, T14
# ---------------------------------------------------------------------------


def test_delete_tool_returns_200(client, engine):
    """對應 T13"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    tool_id = _add_tool(engine, "To Delete")

    # Add a body param
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    db.add(
        ToolBodyParam(
            tool_id=tool_id, param_name="x", param_type="string", is_required=False
        )
    )
    db.commit()
    db.close()

    resp = client.delete(f"/tool/{tool_id}", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    assert resp.json()["message"] == "刪除成功"

    # Verify records are gone
    db = Session_()
    assert db.query(Tool).filter(Tool.id == tool_id).first() is None
    assert db.query(ToolBodyParam).filter(ToolBodyParam.tool_id == tool_id).count() == 0
    db.close()


def test_delete_tool_not_found_returns_404(client, engine):
    """對應 T14"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    resp = client.delete("/tool/99999", headers=_auth_headers(admin_id))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "工具不存在"


def test_delete_tool_no_permission_returns_403(client, engine):
    """未授權 DELETE /tool/{id} 應回 403"""
    user_id, _ = _setup_plain_user(engine, "plain3@test.com")
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    tool_id = _add_tool(engine, "No Delete Tool")

    resp = client.delete(f"/tool/{tool_id}", headers=_auth_headers(user_id))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /tool/test — T15, T16, T17
# ---------------------------------------------------------------------------


def test_tool_test_success(client, engine):
    """對應 T15"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "ok"}

    with patch("app.api.fn_ai_partner_tool.httpx.Client") as mock_client_cls:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.request = MagicMock(return_value=mock_response)
        mock_client_cls.return_value = mock_ctx

        payload = {
            "endpoint_url": "https://httpbin.org/get",
            "http_method": "GET",
            "auth_type": "none",
        }
        resp = client.post("/tool/test", json=payload, headers=_auth_headers(admin_id))

    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "測試完成"
    assert body["data"]["http_status"] == 200
    assert body["data"]["response_body"] == {"result": "ok"}


def test_tool_test_external_returns_401(client, engine):
    """對應 T16"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Unauthorized"}

    with patch("app.api.fn_ai_partner_tool.httpx.Client") as mock_client_cls:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.request = MagicMock(return_value=mock_response)
        mock_client_cls.return_value = mock_ctx

        payload = {
            "endpoint_url": "https://api.example.com/protected",
            "http_method": "GET",
            "auth_type": "none",
        }
        resp = client.post("/tool/test", json=payload, headers=_auth_headers(admin_id))

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["http_status"] == 401
    assert body["data"]["response_body"] == {"error": "Unauthorized"}


def test_tool_test_connection_failure_returns_502(client, engine):
    """對應 T17"""
    import httpx as _httpx

    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    with patch("app.api.fn_ai_partner_tool.httpx.Client") as mock_client_cls:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.request = MagicMock(
            side_effect=_httpx.ConnectError("Connection refused")
        )
        mock_client_cls.return_value = mock_ctx

        payload = {
            "endpoint_url": "https://invalid-host-that-does-not-exist.local/api",
            "http_method": "GET",
            "auth_type": "none",
        }
        resp = client.post("/tool/test", json=payload, headers=_auth_headers(admin_id))

    assert resp.status_code == 502
    assert "外部 API 連線失敗" in resp.json()["detail"]


def test_tool_test_unauthenticated_returns_401(client, engine):
    """未登入 POST /tool/test 應回 401"""
    payload = {
        "endpoint_url": "https://example.com",
        "http_method": "GET",
        "auth_type": "none",
    }
    resp = client.post("/tool/test", json=payload)
    assert resp.status_code == 401


def test_tool_test_no_permission_returns_403(client, engine):
    """無 fn_tool 權限 POST /tool/test 應回 403"""
    user_id, _ = _setup_plain_user(engine, "plain4@test.com")

    payload = {
        "endpoint_url": "https://example.com",
        "http_method": "GET",
        "auth_type": "none",
    }
    resp = client.post("/tool/test", json=payload, headers=_auth_headers(user_id))
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# image_extract 工具 — T20, T21, T22, T23, T24, T25, T26, T27
# ---------------------------------------------------------------------------


def test_add_image_extract_tool_returns_201(client, engine):
    """對應 T20：新增 image_extract 工具成功，tb_tool_image_fields 寫入 2 筆"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "發票擷取工具",
        "description": "從圖片中擷取發票資訊",
        "tool_type": "image_extract",
        "image_fields": [
            {
                "field_name": "invoice_date",
                "field_type": "string",
                "description": "發票日期",
            },
            {
                "field_name": "invoice_amount",
                "field_type": "number",
                "description": "發票金額",
            },
        ],
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"

    # Verify db records
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.name == "發票擷取工具").first()
    assert tool is not None
    assert tool.tool_type == "image_extract"
    assert tool.endpoint_url is None
    assert tool.http_method is None

    fields = db.query(ToolImageField).filter(ToolImageField.tool_id == tool.id).all()
    assert len(fields) == 2

    body_params = db.query(ToolBodyParam).filter(ToolBodyParam.tool_id == tool.id).all()
    assert len(body_params) == 0
    db.close()


def test_add_image_extract_empty_fields_returns_400(client, engine):
    """對應 T21：image_extract 工具 image_fields 為空陣列 → 400"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "空欄位工具",
        "tool_type": "image_extract",
        "image_fields": [],
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "圖片擷取工具至少需設定一個擷取欄位"


def test_add_image_extract_empty_field_name_returns_400(client, engine):
    """對應 T22：image_extract 工具 field_name 為空字串 → 400"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "空名稱欄位工具",
        "tool_type": "image_extract",
        "image_fields": [
            {"field_name": "", "field_type": "string", "description": "測試"},
        ],
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "擷取欄位名稱不可為空"


def test_list_tools_includes_image_fields(client, engine):
    """對應 T23：查詢含 image_fields；external_api 工具的 image_fields 為空陣列"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    _add_tool(engine, "外部 API 工具")
    _add_image_extract_tool(
        engine,
        "圖片擷取工具",
        image_fields=[
            {
                "field_name": "invoice_date",
                "field_type": "string",
                "description": "發票日期",
            },
            {
                "field_name": "invoice_amount",
                "field_type": "number",
                "description": "發票金額",
            },
        ],
    )

    resp = client.get("/tool", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]

    ext_item = next((t for t in data if t["name"] == "外部 API 工具"), None)
    img_item = next((t for t in data if t["name"] == "圖片擷取工具"), None)

    assert ext_item is not None
    assert ext_item["tool_type"] == "external_api"
    assert ext_item["image_fields"] == []

    assert img_item is not None
    assert img_item["tool_type"] == "image_extract"
    assert len(img_item["image_fields"]) == 2
    field_names = [f["field_name"] for f in img_item["image_fields"]]
    assert "invoice_date" in field_names
    assert "invoice_amount" in field_names


def test_list_tools_unauthenticated_returns_401_v2(client, engine):
    """對應 T24：未登入 GET /tool → 401"""
    resp = client.get("/tool")
    assert resp.status_code == 401


def test_list_tools_no_fn_permission_returns_403(client, engine):
    """對應 T25：已登入但不具備 fn_ai_partner_tool 功能權限 → 403"""
    user_id, _ = _setup_plain_user(engine, "plain5@test.com")
    resp = client.get("/tool", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_update_image_extract_tool_returns_200(client, engine):
    """對應 T26：修改 image_extract 工具成功；image_fields 清除重寫 3 筆；tool_type 不變"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    tool_id = _add_image_extract_tool(
        engine,
        "待更新圖片工具",
        image_fields=[
            {"field_name": "field1", "field_type": "string"},
            {"field_name": "field2", "field_type": "number"},
        ],
    )

    payload = {
        "name": "待更新圖片工具",
        "tool_type": "external_api",  # 即使傳入不同 tool_type，後端應忽略
        "image_fields": [
            {
                "field_name": "new_field1",
                "field_type": "string",
                "description": "第一欄",
            },
            {
                "field_name": "new_field2",
                "field_type": "number",
                "description": "第二欄",
            },
            {
                "field_name": "new_field3",
                "field_type": "boolean",
                "description": "第三欄",
            },
        ],
    }
    resp = client.patch(
        f"/tool/{tool_id}", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    # Verify db: tool_type unchanged, image_fields rewritten with 3 rows
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    assert tool.tool_type == "image_extract"
    fields = db.query(ToolImageField).filter(ToolImageField.tool_id == tool_id).all()
    assert len(fields) == 3
    db.close()


def test_update_image_extract_empty_fields_returns_400(client, engine):
    """對應 T27：修改 image_extract 工具時 image_fields 為空陣列 → 400"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    tool_id = _add_image_extract_tool(
        engine,
        "待測試圖片工具",
        image_fields=[{"field_name": "field1", "field_type": "string"}],
    )

    payload = {
        "name": "待測試圖片工具",
        "image_fields": [],
    }
    resp = client.patch(
        f"/tool/{tool_id}", json=payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "圖片擷取工具至少需設定一個擷取欄位"
