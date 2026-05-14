"""
Tests for fn_ai_partner_tool APIs:
  GET    /tool
  POST   /tool
  PATCH  /tool/{id}
  DELETE /tool/{id}
  POST   /tool/test

  Also covers ai_agent.py web_scraper tool execution.
"""

import os
from unittest.mock import MagicMock, patch

import httpx
from sqlalchemy.orm import Session, sessionmaker

from app.db.models.fn_ai_partner_tool import Tool, ToolBodyParam, ToolWebScraperConfig
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


def _add_web_scraper_tool(
    engine,
    name: str,
    target_url: str = "https://example.com",
    extract_description: str = "test",
    max_chars: int = 4000,
) -> int:
    """Insert a web_scraper tool directly. Return tool id."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = Tool(
        name=name,
        tool_type="web_scraper",
        endpoint_url=None,
        http_method=None,
        auth_type="none",
    )
    db.add(tool)
    db.flush()
    config = ToolWebScraperConfig(
        tool_id=tool.id,
        target_url=target_url,
        extract_description=extract_description,
        max_chars=max_chars,
    )
    db.add(config)
    db.commit()
    tid = tool.id
    db.close()
    return tid


# ---------------------------------------------------------------------------
# GET /tool — T1, T2, T3 (test_api.md T1, T2, T3)
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
    """對應 T24（未登入 GET /tool 應回 401）"""
    resp = client.get("/tool")
    assert resp.status_code == 401


def test_list_tools_fn_permission_403(client, engine):
    """對應 T25（已登入但不具備功能權限）"""
    user_id, _ = _setup_plain_user(engine, "plain5@test.com")
    resp = client.get("/tool", headers=_auth_headers(user_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


# ---------------------------------------------------------------------------
# POST /tool — T4, T5, T6, T7, T8, T9
# ---------------------------------------------------------------------------


def test_add_tool_returns_201(client, engine):
    """對應 T4"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "My Tool",
        "tool_type": "external_api",
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
        "tool_type": "external_api",
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
        "tool_type": "external_api",
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
        "tool_type": "external_api",
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
        "tool_type": "external_api",
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
        "tool_type": "external_api",
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
        "tool_type": "external_api",
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
        "tool_type": "external_api",
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
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    with patch("app.api.fn_ai_partner_tool.httpx.Client") as mock_client_cls:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.request = MagicMock(
            side_effect=httpx.ConnectError("Connection refused")
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
# image_extract 類型工具 — T20, T21, T22, T23, T26, T27
# ---------------------------------------------------------------------------


def test_add_image_extract_tool_returns_201(client, engine):
    """對應 T20"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "圖片擷取工具",
        "tool_type": "image_extract",
        "image_fields": [
            {
                "field_name": "invoice_date",
                "field_type": "string",
                "description": "日期",
            },
            {
                "field_name": "invoice_amount",
                "field_type": "number",
                "description": "金額",
            },
        ],
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"


def test_add_image_extract_empty_fields_returns_400(client, engine):
    """對應 T21"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "Empty Fields Tool",
        "tool_type": "image_extract",
        "image_fields": [],
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "圖片擷取工具至少需設定一個擷取欄位"


def test_add_image_extract_empty_field_name_returns_400(client, engine):
    """對應 T22"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "Bad Field Name Tool",
        "tool_type": "image_extract",
        "image_fields": [
            {"field_name": "", "field_type": "string", "description": "test"},
        ],
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "擷取欄位名稱不可為空"


def test_list_tools_contains_image_fields(client, engine):
    """對應 T23"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    # Add image_extract tool
    payload = {
        "name": "ImageTool",
        "tool_type": "image_extract",
        "image_fields": [
            {"field_name": "date", "field_type": "string", "description": "日期"},
            {"field_name": "amount", "field_type": "number", "description": "金額"},
        ],
    }
    client.post("/tool", json=payload, headers=_auth_headers(admin_id))

    resp = client.get("/tool", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    image_tool = next((t for t in data if t["name"] == "ImageTool"), None)
    assert image_tool is not None
    assert image_tool["tool_type"] == "image_extract"
    assert len(image_tool["image_fields"]) == 2
    assert image_tool["web_scraper_config"] is None


def test_update_image_extract_tool_returns_200(client, engine):
    """對應 T26"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    # Create image_extract tool
    post_payload = {
        "name": "Update Image Tool",
        "tool_type": "image_extract",
        "image_fields": [
            {"field_name": "old_field", "field_type": "string"},
        ],
    }
    client.post("/tool", json=post_payload, headers=_auth_headers(admin_id))

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.name == "Update Image Tool").first()
    tool_id = tool.id
    db.close()

    # Update with new fields and even pass tool_type (should be ignored)
    patch_payload = {
        "name": "Update Image Tool",
        "tool_type": "external_api",  # should be ignored
        "image_fields": [
            {"field_name": "f1", "field_type": "string"},
            {"field_name": "f2", "field_type": "number"},
            {"field_name": "f3", "field_type": "boolean"},
        ],
    }
    resp = client.patch(
        f"/tool/{tool_id}", json=patch_payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    # Verify tool_type unchanged and image_fields updated
    db = Session_()
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    assert tool.tool_type == "image_extract"
    from app.db.models.fn_ai_partner_tool import ToolImageField

    fields = db.query(ToolImageField).filter(ToolImageField.tool_id == tool_id).all()
    assert len(fields) == 3
    db.close()


def test_update_image_extract_empty_fields_returns_400(client, engine):
    """對應 T27"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    post_payload = {
        "name": "Image Tool T27",
        "tool_type": "image_extract",
        "image_fields": [{"field_name": "f1", "field_type": "string"}],
    }
    client.post("/tool", json=post_payload, headers=_auth_headers(admin_id))

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.name == "Image Tool T27").first()
    tool_id = tool.id
    db.close()

    patch_payload = {
        "name": "Image Tool T27",
        "image_fields": [],
    }
    resp = client.patch(
        f"/tool/{tool_id}", json=patch_payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "圖片擷取工具至少需設定一個擷取欄位"


# ---------------------------------------------------------------------------
# web_scraper 類型工具 — T28, T29, T30, T31, T32, T33, T34
# ---------------------------------------------------------------------------


def test_add_web_scraper_tool_default_max_chars(client, engine):
    """對應 T28（test_api.md）- web_scraper 新增成功，max_chars 省略預設 4000"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "匯率查詢工具",
        "tool_type": "web_scraper",
        "target_url": "https://rate.bot.com.tw/xrt",
        "extract_description": "台銀美元買入匯率",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201
    assert resp.json()["message"] == "新增成功"

    # Verify DB
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.name == "匯率查詢工具").first()
    assert tool is not None
    assert tool.tool_type == "web_scraper"
    assert tool.endpoint_url is None
    assert tool.http_method is None
    assert tool.auth_type == "none"

    config = (
        db.query(ToolWebScraperConfig)
        .filter(ToolWebScraperConfig.tool_id == tool.id)
        .first()
    )
    assert config is not None
    assert config.target_url == "https://rate.bot.com.tw/xrt"
    assert config.extract_description == "台銀美元買入匯率"
    assert config.max_chars == 4000
    db.close()


def test_add_web_scraper_empty_target_url_returns_400(client, engine):
    """對應 T29（test_api.md）- target_url 為空 → 400"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "Web Scraper Bad",
        "tool_type": "web_scraper",
        "target_url": "",
        "extract_description": "台銀美元買入匯率",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "目標網址為必填"


def test_add_web_scraper_empty_extract_description_returns_400(client, engine):
    """對應 T30（test_api.md）- extract_description 為空 → 400"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "Web Scraper No Desc",
        "tool_type": "web_scraper",
        "target_url": "https://example.com",
        "extract_description": "",
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 400
    assert resp.json()["detail"] == "擷取描述為必填"


def test_add_web_scraper_custom_max_chars(client, engine):
    """對應 T31（test_api.md）- 指定 max_chars=1000"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    payload = {
        "name": "Custom MaxChars Tool",
        "tool_type": "web_scraper",
        "target_url": "https://example.com",
        "extract_description": "test description",
        "max_chars": 1000,
    }
    resp = client.post("/tool", json=payload, headers=_auth_headers(admin_id))
    assert resp.status_code == 201

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.name == "Custom MaxChars Tool").first()
    config = (
        db.query(ToolWebScraperConfig)
        .filter(ToolWebScraperConfig.tool_id == tool.id)
        .first()
    )
    assert config.max_chars == 1000
    db.close()


def test_list_tools_returns_web_scraper_config(client, engine):
    """對應 T32（test_api.md）- GET /tool 回傳 web_scraper_config 物件；其他類型為 null"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)

    # Add web_scraper tool
    ws_payload = {
        "name": "WebScraper Tool",
        "tool_type": "web_scraper",
        "target_url": "https://example.com",
        "extract_description": "test",
        "max_chars": 2000,
    }
    client.post("/tool", json=ws_payload, headers=_auth_headers(admin_id))

    # Add external_api tool
    ext_payload = {
        "name": "External API Tool",
        "tool_type": "external_api",
        "endpoint_url": "https://api.example.com",
        "http_method": "GET",
        "auth_type": "none",
    }
    client.post("/tool", json=ext_payload, headers=_auth_headers(admin_id))

    resp = client.get("/tool", headers=_auth_headers(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]

    ws_item = next((t for t in data if t["name"] == "WebScraper Tool"), None)
    ext_item = next((t for t in data if t["name"] == "External API Tool"), None)

    assert ws_item is not None
    assert ws_item["tool_type"] == "web_scraper"
    assert ws_item["web_scraper_config"] is not None
    assert ws_item["web_scraper_config"]["target_url"] == "https://example.com"
    assert ws_item["web_scraper_config"]["extract_description"] == "test"
    assert ws_item["web_scraper_config"]["max_chars"] == 2000

    assert ext_item is not None
    assert ext_item["web_scraper_config"] is None


def test_update_web_scraper_tool_returns_200(client, engine):
    """對應 T33（test_api.md）- 修改 web_scraper 工具成功，tool_type 不可變"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    tool_id = _add_web_scraper_tool(
        engine, "WebScraper Update", extract_description="original desc"
    )

    patch_payload = {
        "name": "WebScraper Update",
        "tool_type": "external_api",  # should be ignored
        "target_url": "https://new.example.com",
        "extract_description": "updated desc",
        "max_chars": 3000,
    }
    resp = client.patch(
        f"/tool/{tool_id}", json=patch_payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "更新成功"

    Session_ = sessionmaker(bind=engine)
    db = Session_()
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    assert tool.tool_type == "web_scraper"  # unchanged
    config = (
        db.query(ToolWebScraperConfig)
        .filter(ToolWebScraperConfig.tool_id == tool_id)
        .first()
    )
    assert config.extract_description == "updated desc"
    assert config.max_chars == 3000
    db.close()


def test_update_web_scraper_empty_target_url_returns_400(client, engine):
    """對應 T34（test_api.md）- 修改 web_scraper 時 target_url 為空 → 400"""
    admin_id, _, _ = _setup_admin_with_fn_tool(engine)
    tool_id = _add_web_scraper_tool(engine, "WebScraper T34")

    patch_payload = {
        "name": "WebScraper T34",
        "target_url": "",
        "extract_description": "some desc",
    }
    resp = client.patch(
        f"/tool/{tool_id}", json=patch_payload, headers=_auth_headers(admin_id)
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "目標網址為必填"


# ---------------------------------------------------------------------------
# AI Agent web_scraper 工具執行 — T15, T16, T17 (agentic loop)
# ---------------------------------------------------------------------------


def test_ai_agent_web_scraper_success():
    """對應 T15 — AI Agent web_scraper 成功擷取並由 LLM 解讀"""
    from app.services import ai_agent

    mock_resp = MagicMock()
    mock_resp.text = "<html><body><p>台銀美元買入匯率：31.5</p></body></html>"

    mock_llm_result = {"content": "台銀美元買入匯率為 31.5", "tool_calls": []}

    tool_config = {
        "name": "rate_tool",
        "tool_type": "web_scraper",
        "target_url": "https://rate.bot.com.tw/xrt",
        "extract_description": "台銀美元買入匯率",
        "max_chars": 4000,
    }

    with (
        patch("app.services.ai_agent.httpx.Client") as mock_client_cls,
        patch("app.services.ai_agent.chat", return_value=mock_llm_result),
    ):
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.get = MagicMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_ctx

        result = ai_agent._execute_web_scraper(tool_config, {})

    assert result == "台銀美元買入匯率為 31.5"


def test_ai_agent_web_scraper_connect_error():
    """對應 T16 — AI Agent web_scraper ConnectError 時回傳錯誤訊息，不 raise"""
    from app.services import ai_agent

    tool_config = {
        "name": "rate_tool",
        "tool_type": "web_scraper",
        "target_url": "https://unreachable.local",
        "extract_description": "台銀美元買入匯率",
        "max_chars": 4000,
    }

    with patch("app.services.ai_agent.httpx.Client") as mock_client_cls:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.get = MagicMock(side_effect=httpx.ConnectError("connection refused"))
        mock_client_cls.return_value = mock_ctx

        result = ai_agent._execute_web_scraper(tool_config, {})

    assert result == "無法連線至目標網址"


def test_ai_agent_web_scraper_timeout_error():
    """對應 T17 — AI Agent web_scraper TimeoutException 時回傳錯誤訊息，不 raise"""
    from app.services import ai_agent

    tool_config = {
        "name": "rate_tool",
        "tool_type": "web_scraper",
        "target_url": "https://slow.local",
        "extract_description": "台銀美元買入匯率",
        "max_chars": 4000,
    }

    with patch("app.services.ai_agent.httpx.Client") as mock_client_cls:
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        mock_ctx.get = MagicMock(
            side_effect=httpx.TimeoutException("timeout", request=MagicMock())
        )
        mock_client_cls.return_value = mock_ctx

        result = ai_agent._execute_web_scraper(tool_config, {})

    assert result == "目標網址請求逾時"
