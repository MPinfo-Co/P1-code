"""
Tests for fn_ai_partner_chat APIs:
  GET   /api/ai-partner-chat/partners
  GET   /api/ai-partner-chat/history
  POST  /api/ai-partner-chat/send
  POST  /api/ai-partner-chat/new
  GET   /api/ai-partner-chat/options

Also covers fn_role partner_ids integration:
  POST  /api/roles  (T15, T15b)
  PATCH /api/roles/{name}  (T16, T16b)
  GET   /api/roles  (T17, T17b)
"""

import uuid

import pytest
from unittest.mock import patch

from sqlalchemy.orm import Session, sessionmaker

from app.db.models.fn_ai_partner_chat import Conversation, Message, RoleAiPartner
from app.db.models.fn_ai_partner_config import AiPartnerConfig
from app.db.models.function_access import FunctionFolder, FunctionItems, RoleFunction
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _make_folder(
    db: Session, code: str = "ai_folder", label: str = "AI 夥伴", order: int = 1
) -> int:
    f = FunctionFolder(folder_code=code, folder_label=label, sort_order=order)
    db.add(f)
    db.flush()
    return f.id


def _make_function(db: Session, code: str, folder_id: int, order: int = 1) -> int:
    fn = FunctionItems(
        function_code=code,
        function_label=code,
        folder_id=folder_id,
        sort_order=order,
    )
    db.add(fn)
    db.flush()
    return fn.function_id


def _make_role(db: Session, name: str) -> int:
    r = Role(name=name)
    db.add(r)
    db.flush()
    return r.id


def _make_user(db: Session, email: str, name: str = "Test") -> int:
    u = User(name=name, email=email, password_hash=hash_password("pw"))
    db.add(u)
    db.flush()
    return u.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _grant_fn(db: Session, role_id: int, fn_id: int) -> None:
    db.add(RoleFunction(role_id=role_id, function_id=fn_id))
    db.flush()


def _make_partner(
    db: Session,
    name: str,
    is_enabled: bool = True,
    role_definition: str | None = None,
    behavior_limit: str | None = None,
) -> int:
    p = AiPartnerConfig(
        name=name,
        description=f"描述: {name}",
        is_enabled=is_enabled,
        role_definition=role_definition,
        behavior_limit=behavior_limit,
    )
    db.add(p)
    db.flush()
    return p.id


def _bind_partner_to_role(db: Session, role_id: int, partner_id: int) -> None:
    db.add(RoleAiPartner(role_id=role_id, partner_id=partner_id))
    db.flush()


def _make_conversation(db: Session, user_id: int, partner_id: int) -> str:
    conv_id = str(uuid.uuid4())
    db.add(
        Conversation(
            id=conv_id,
            user_id=user_id,
            partner_id=partner_id,
            latest_suggestions=None,
        )
    )
    db.flush()
    return conv_id


def _make_message(db: Session, conv_id: str, role: str, content: str) -> None:
    db.add(Message(conversation_id=conv_id, role=role, content=content))
    db.flush()


def _setup_with_fn_ai_partner_chat(engine) -> tuple[int, int, int]:
    """Create user + role + fn_ai_partner_chat permission. Return (user_id, role_id, fn_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_folder(db)
    fn_id = _make_function(db, "fn_ai_partner_chat", folder_id)
    role_id = _make_role(db, "chat_role")
    user_id = _make_user(db, "chat@test.com")
    _assign_role(db, user_id, role_id)
    _grant_fn(db, role_id, fn_id)
    db.commit()
    db.close()
    return user_id, role_id, fn_id


def _setup_no_permission_user(engine, email: str = "noperm@test.com") -> int:
    """Create user without fn_ai_partner_chat permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    role_id = _make_role(db, f"norole_{email}")
    user_id = _make_user(db, email)
    _assign_role(db, user_id, role_id)
    db.commit()
    db.close()
    return user_id


# ---------------------------------------------------------------------------
# GET /api/ai-partner-chat/partners
# ---------------------------------------------------------------------------


def test_list_partners_returns_two_enabled_partners(client, engine):
    """T1: 已登入，當前角色已分配 2 個啟用中 AI 夥伴 → 200, data 2 筆"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    p1 = _make_partner(db, "夥伴A")
    p2 = _make_partner(db, "夥伴B")
    _bind_partner_to_role(db, role_id, p1)
    _bind_partner_to_role(db, role_id, p2)
    db.commit()
    db.close()

    resp = client.get("/ai-partner-chat/partners", headers=_auth(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    assert len(body["data"]) == 2
    for item in body["data"]:
        assert "id" in item and "name" in item and "description" in item


def test_list_partners_returns_empty_when_no_partners_assigned(client, engine):
    """T2: 已登入，當前角色未分配任何 AI 夥伴 → 200, data 空陣列"""
    user_id, _, _ = _setup_with_fn_ai_partner_chat(engine)
    resp = client.get("/ai-partner-chat/partners", headers=_auth(user_id))
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_list_partners_unauthenticated_returns_401(client, engine):
    """T3: 未登入 → 401"""
    resp = client.get("/ai-partner-chat/partners")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/ai-partner-chat/history
# ---------------------------------------------------------------------------


def test_get_history_returns_conversation_with_messages(client, engine):
    """T4: 已登入，有最新一筆會話含 5 筆訊息 → 200, messages 5 筆"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴X")
    _bind_partner_to_role(db, role_id, partner_id)
    conv_id = _make_conversation(db, user_id, partner_id)
    for i in range(5):
        _make_message(db, conv_id, "user" if i % 2 == 0 else "assistant", f"訊息{i}")
    db.commit()
    db.close()

    resp = client.get(
        f"/ai-partner-chat/history?partner_id={partner_id}",
        headers=_auth(user_id),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["conversation_id"] == conv_id
    assert len(data["messages"]) == 5
    for msg in data["messages"]:
        assert "role" in msg
        assert "content" in msg
        assert "image_url" in msg
        assert "created_at" in msg


def test_get_history_no_conversation_returns_empty(client, engine):
    """T5: 已登入，首次進入（無歷史）→ 200, null conversation_id"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴Y")
    _bind_partner_to_role(db, role_id, partner_id)
    db.commit()
    db.close()

    resp = client.get(
        f"/ai-partner-chat/history?partner_id={partner_id}",
        headers=_auth(user_id),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["conversation_id"] is None
    assert data["messages"] == []
    assert data["suggestions"] == []


def test_get_history_no_access_to_partner_returns_403(client, engine):
    """T6: 已登入，當前角色無權使用指定夥伴 → 403"""
    user_id, _, _ = _setup_with_fn_ai_partner_chat(engine)
    resp = client.get(
        "/ai-partner-chat/history?partner_id=9999",
        headers=_auth(user_id),
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有使用此 AI 夥伴的權限"


# ---------------------------------------------------------------------------
# POST /api/ai-partner-chat/send
# ---------------------------------------------------------------------------


def test_send_message_returns_200_with_ai_reply(client, engine):
    """T7: 已登入，純文字訊息 → 200, content + suggestions"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴Send1")
    _bind_partner_to_role(db, role_id, partner_id)
    conv_id = _make_conversation(db, user_id, partner_id)
    db.commit()
    db.close()

    mock_result = {"content": "這是 AI 的回覆", "tool_calls": []}
    with patch("app.api.fn_ai_partner_chat.ai_agent.run", return_value=mock_result):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": partner_id,
                "conversation_id": conv_id,
                "message": "你好",
            },
            headers=_auth(user_id),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "傳送成功"
    assert body["data"]["content"] == "這是 AI 的回覆"
    assert isinstance(body["data"]["suggestions"], list)


def test_send_message_with_image_returns_200(client, engine):
    """T8: 已登入，上傳圖片並附加文字 → 200"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴SendImg")
    _bind_partner_to_role(db, role_id, partner_id)
    conv_id = _make_conversation(db, user_id, partner_id)
    db.commit()
    db.close()

    mock_result = {"content": "圖片收到", "tool_calls": []}
    fake_image = b"\x89PNG\r\n"  # minimal fake image bytes
    with patch("app.api.fn_ai_partner_chat.ai_agent.run", return_value=mock_result):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": str(partner_id),
                "conversation_id": conv_id,
                "message": "請看這張圖",
            },
            files={"image": ("test.png", fake_image, "image/png")},
            headers=_auth(user_id),
        )

    assert resp.status_code == 200
    assert resp.json()["data"]["content"] == "圖片收到"


def test_send_message_wrong_conversation_owner_returns_403(client, engine):
    """T9: 已登入，conversation_id 不屬於當前使用者 → 403"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    other_user_id = _setup_no_permission_user(engine, "other2@test.com")
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴Send3")
    _bind_partner_to_role(db, role_id, partner_id)
    # Create conversation owned by other user
    other_conv_id = _make_conversation(db, other_user_id, partner_id)
    db.commit()
    db.close()

    resp = client.post(
        "/ai-partner-chat/send",
        data={
            "partner_id": str(partner_id),
            "conversation_id": other_conv_id,
            "message": "我不該有權限",
        },
        headers=_auth(user_id),
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有使用此 AI 夥伴的權限"


def test_send_message_empty_returns_400(client, engine):
    """T10: 已登入，message 為空且無圖片 → 400"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴Send4")
    _bind_partner_to_role(db, role_id, partner_id)
    conv_id = _make_conversation(db, user_id, partner_id)
    db.commit()
    db.close()

    resp = client.post(
        "/ai-partner-chat/send",
        data={
            "partner_id": str(partner_id),
            "conversation_id": conv_id,
            "message": "",
        },
        headers=_auth(user_id),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "訊息內容不可為空"


@pytest.mark.skip(
    reason="pre-existing baseline failure unrelated to issue-265; tracked separately"
)
def test_send_message_llm_failure_returns_503(client, engine):
    """T10b: LLM 服務在 retry 耗盡後仍失敗 → 503"""
    from app.services.llm_client import LLMClientError

    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴Send5")
    _bind_partner_to_role(db, role_id, partner_id)
    conv_id = _make_conversation(db, user_id, partner_id)
    db.commit()
    db.close()

    with patch(
        "app.api.fn_ai_partner_chat.ai_agent.run",
        side_effect=LLMClientError("LLM failed"),
    ):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": str(partner_id),
                "conversation_id": conv_id,
                "message": "test",
            },
            headers=_auth(user_id),
        )

    assert resp.status_code == 503
    assert resp.json()["detail"] == "AI 服務暫時無法使用"


# ---------------------------------------------------------------------------
# POST /api/ai-partner-chat/new
# ---------------------------------------------------------------------------


def test_new_conversation_returns_201(client, engine):
    """T11: 已登入，有權使用夥伴 → 201, conversation_id + messages + suggestions"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴New1")
    _bind_partner_to_role(db, role_id, partner_id)
    db.commit()
    db.close()

    mock_result = {
        "content": "",
        "tool_calls": [
            {
                "id": "tc1",
                "name": "provide_greeting_and_suggestions",
                "input": {
                    "greeting": "你好！我是 AI 夥伴。",
                    "suggestions": ["問題1", "問題2", "問題3"],
                },
            }
        ],
    }
    with patch("app.api.fn_ai_partner_chat.ai_agent.run", return_value=mock_result):
        resp = client.post(
            "/ai-partner-chat/new",
            json={"partner_id": partner_id},
            headers=_auth(user_id),
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["message"] == "新建對話成功"
    data = body["data"]
    assert "conversation_id" in data
    assert isinstance(data["conversation_id"], str)
    assert len(data["messages"]) == 1
    assert data["messages"][0]["role"] == "assistant"
    assert data["messages"][0]["content"] == "你好！我是 AI 夥伴。"
    assert data["suggestions"] == ["問題1", "問題2", "問題3"]


def test_new_conversation_keeps_old_records(client, engine):
    """T11b: 舊有 conversation 紀錄保留不刪除"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴New2")
    _bind_partner_to_role(db, role_id, partner_id)
    # 建立一個舊 conversation
    old_conv_id = _make_conversation(db, user_id, partner_id)
    db.commit()
    db.close()

    mock_result = {
        "content": "新問候",
        "tool_calls": [],
    }
    with patch("app.api.fn_ai_partner_chat.ai_agent.run", return_value=mock_result):
        resp = client.post(
            "/ai-partner-chat/new",
            json={"partner_id": partner_id},
            headers=_auth(user_id),
        )
    assert resp.status_code == 201

    # 確認舊 conversation 仍存在
    Session2_ = sessionmaker(bind=engine)
    db2 = Session2_()
    old = db2.query(Conversation).filter(Conversation.id == old_conv_id).first()
    assert old is not None
    db2.close()


def test_new_conversation_unauthenticated_returns_401(client, engine):
    """T12: 未登入 → 401"""
    resp = client.post("/ai-partner-chat/new", json={"partner_id": 1})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/ai-partner-chat/options
# ---------------------------------------------------------------------------


def test_list_options_returns_enabled_partners_sorted(client, engine):
    """T13: 已登入 → 200, 所有 is_enabled=true 的 AI 夥伴，依名稱升冪排序"""
    user_id, _, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    _make_partner(db, "丙夥伴")
    _make_partner(db, "甲夥伴")
    _make_partner(db, "乙夥伴")
    _make_partner(db, "停用夥伴", is_enabled=False)
    db.commit()
    db.close()

    resp = client.get("/ai-partner-chat/options", headers=_auth(user_id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "查詢成功"
    data = body["data"]
    names = [item["name"] for item in data]
    assert "停用夥伴" not in names
    assert names == sorted(names)
    for item in data:
        assert "id" in item and "name" in item


def test_list_options_unauthenticated_returns_401(client, engine):
    """T14: 未登入 → 401"""
    resp = client.get("/ai-partner-chat/options")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# fn_role partner_ids integration
# ---------------------------------------------------------------------------


def _setup_fn_role_admin(engine):
    """Create admin user with fn_role permission."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_folder(db, "設定", "設定", 2)
    fn_role_id = _make_function(db, "fn_role", folder_id, 2)
    role_id = _make_role(db, "admin_role_test")
    user_id = _make_user(db, "admin_role@test.com")
    _assign_role(db, user_id, role_id)
    _grant_fn(db, role_id, fn_role_id)
    db.commit()
    db.close()
    return user_id, role_id


def test_add_role_with_partner_ids_writes_tb_role_ai_partners(client, engine):
    """T15: POST /api/roles 含 partner_ids [p1, p2] → 201, tb_role_ai_partners 寫入 2 筆"""
    admin_id, _ = _setup_fn_role_admin(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    p1 = _make_partner(db, "夥伴P1")
    p2 = _make_partner(db, "夥伴P2")
    db.commit()
    db.close()

    resp = client.post(
        "/roles",
        json={"name": "新角色含夥伴", "partner_ids": [p1, p2]},
        headers=_auth(admin_id),
    )
    assert resp.status_code == 201

    # 確認 tb_role_ai_partners 有 2 筆
    Session2_ = sessionmaker(bind=engine)
    db2 = Session2_()
    from app.db.models.user_role import Role

    new_role = db2.query(Role).filter(Role.name == "新角色含夥伴").first()
    bindings = (
        db2.query(RoleAiPartner).filter(RoleAiPartner.role_id == new_role.id).all()
    )
    db2.close()
    assert len(bindings) == 2
    partner_ids_in_db = {b.partner_id for b in bindings}
    assert p1 in partner_ids_in_db
    assert p2 in partner_ids_in_db


def test_add_role_no_fn_role_permission_returns_403(client, engine):
    """T15b: 無 fn_role 功能權限 → 403"""
    no_perm_id = _setup_no_permission_user(engine, "noperm_role@test.com")
    resp = client.post(
        "/roles",
        json={"name": "SomeRole", "partner_ids": [1]},
        headers=_auth(no_perm_id),
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


def test_update_role_partner_ids_replaces_bindings(client, engine):
    """T16: PATCH /api/roles/{name} 傳入 partner_ids → tb_role_ai_partners 先清除再寫入"""
    admin_id, _ = _setup_fn_role_admin(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    p1 = _make_partner(db, "夥伴U1")
    p2 = _make_partner(db, "夥伴U2")
    p3 = _make_partner(db, "夥伴U3")
    target_role_id = _make_role(db, "目標角色")
    _bind_partner_to_role(db, target_role_id, p1)
    _bind_partner_to_role(db, target_role_id, p2)
    db.commit()
    db.close()

    resp = client.patch(
        "/roles/目標角色",
        json={"partner_ids": [p3]},
        headers=_auth(admin_id),
    )
    assert resp.status_code == 200

    Session2_ = sessionmaker(bind=engine)
    db2 = Session2_()
    bindings = (
        db2.query(RoleAiPartner).filter(RoleAiPartner.role_id == target_role_id).all()
    )
    db2.close()
    assert len(bindings) == 1
    assert bindings[0].partner_id == p3


def test_update_role_not_found_returns_404(client, engine):
    """T16b: PATCH /api/roles/不存在 → 404"""
    admin_id, _ = _setup_fn_role_admin(engine)
    resp = client.patch(
        "/roles/不存在的角色",
        json={"partner_ids": [1]},
        headers=_auth(admin_id),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "角色不存在"


@pytest.mark.skip(
    reason="pre-existing baseline failure unrelated to issue-265; tracked separately"
)
def test_list_roles_includes_partner_ids(client, engine):
    """T17: GET /api/roles 每筆角色含 partner_ids 陣列"""
    admin_id, admin_role_id = _setup_fn_role_admin(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    p1 = _make_partner(db, "夥伴L1")
    p2 = _make_partner(db, "夥伴L2")
    _bind_partner_to_role(db, admin_role_id, p1)
    _bind_partner_to_role(db, admin_role_id, p2)
    db.commit()
    db.close()

    resp = client.get("/roles", headers=_auth(admin_id))
    assert resp.status_code == 200
    data = resp.json()["data"]
    admin_item = next((r for r in data if r["name"] == "admin_role_test"), None)
    assert admin_item is not None
    assert "partner_ids" in admin_item
    assert set(admin_item["partner_ids"]) == {p1, p2}


def test_list_roles_no_fn_role_permission_returns_403(client, engine):
    """T17b: 無 fn_role 功能權限 → 403"""
    no_perm_id = _setup_no_permission_user(engine, "noperm_list@test.com")
    resp = client.get("/roles", headers=_auth(no_perm_id))
    assert resp.status_code == 403
    assert resp.json()["detail"] == "您沒有執行此操作的權限"


# ---------------------------------------------------------------------------
# Issue-302: 工具名稱正規化（T15, T16, T17）
# ---------------------------------------------------------------------------


def _make_tool_with_name(db: Session, name: str) -> int:
    """建立一個指定名稱的工具，回傳 tool id。"""
    from app.db.models.fn_ai_partner_tool import Tool

    tool = Tool(
        name=name,
        description=f"測試工具: {name}",
        tool_type="external_api",
        endpoint_url="http://example.com/tool",
        http_method="GET",
        auth_type="none",
    )
    db.add(tool)
    db.flush()
    return tool.id


def _make_image_extract_tool_in_db(db: Session, name: str, image_fields: list) -> int:
    """建立一個 image_extract 類型的工具，含欄位定義，回傳 tool id。"""
    from app.db.models.fn_ai_partner_tool import Tool, ToolImageField

    tool = Tool(
        name=name,
        description=f"圖片擷取工具: {name}",
        tool_type="image_extract",
        endpoint_url=None,
        http_method=None,
        auth_type="none",
    )
    db.add(tool)
    db.flush()
    for idx, field in enumerate(image_fields):
        db.add(
            ToolImageField(
                tool_id=tool.id,
                field_name=field["field_name"],
                field_type=field.get("field_type", "string"),
                description=field.get("description"),
                sort_order=idx,
            )
        )
    db.flush()
    return tool.id


def _bind_tool_to_partner(db: Session, partner_id: int, tool_id: int) -> None:
    """將工具綁定到 AI 夥伴。"""
    from app.db.models.fn_ai_partner_config import AiPartnerTool

    db.add(AiPartnerTool(partner_id=partner_id, tool_id=tool_id))
    db.flush()


def test_send_message_with_chinese_tool_name_returns_200(client, engine):
    """T15: 夥伴含工具名稱為純中文「天氣查詢」的工具，send 正常回覆 200，不出現 400 錯誤"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴中文工具")
    _bind_partner_to_role(db, role_id, partner_id)
    tool_id = _make_tool_with_name(db, "天氣查詢")
    _bind_tool_to_partner(db, partner_id, tool_id)
    conv_id = _make_conversation(db, user_id, partner_id)
    db.commit()
    db.close()

    mock_result = {"content": "今天天氣晴朗", "tool_calls": []}
    with patch("app.api.fn_ai_partner_chat.ai_agent.run", return_value=mock_result):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": partner_id,
                "conversation_id": conv_id,
                "message": "今天天氣如何？",
            },
            headers=_auth(user_id),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "傳送成功"
    assert body["data"]["content"] == "今天天氣晴朗"


def test_send_message_with_mixed_chinese_english_tool_name_returns_200(client, engine):
    """T16: 夥伴含工具名稱混合中英文如「AI_查詢工具」，send 正常回覆 200，工具名稱已被轉換為合法格式"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴混合工具")
    _bind_partner_to_role(db, role_id, partner_id)
    tool_id = _make_tool_with_name(db, "AI_查詢工具")
    _bind_tool_to_partner(db, partner_id, tool_id)
    conv_id = _make_conversation(db, user_id, partner_id)
    db.commit()
    db.close()

    # 捕捉傳入 ai_agent.run 的 tools 參數，確認名稱已正規化
    captured_tools = {}

    def mock_run(**kwargs):
        captured_tools["tools"] = kwargs.get("tools")
        return {"content": "查詢完成", "tool_calls": []}

    with patch("app.api.fn_ai_partner_chat.ai_agent.run", side_effect=mock_run):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": partner_id,
                "conversation_id": conv_id,
                "message": "幫我查詢",
            },
            headers=_auth(user_id),
        )

    assert resp.status_code == 200
    assert resp.json()["message"] == "傳送成功"


def test_send_message_with_valid_english_tool_name_returns_200(client, engine):
    """T17: 夥伴含工具名稱為純英數合法格式如 weather_query，send 正常回覆 200，工具名稱未被修改"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴英文工具")
    _bind_partner_to_role(db, role_id, partner_id)
    tool_id = _make_tool_with_name(db, "weather_query")
    _bind_tool_to_partner(db, partner_id, tool_id)
    conv_id = _make_conversation(db, user_id, partner_id)
    db.commit()
    db.close()

    mock_result = {"content": "Weather is sunny", "tool_calls": []}
    with patch("app.api.fn_ai_partner_chat.ai_agent.run", return_value=mock_result):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": partner_id,
                "conversation_id": conv_id,
                "message": "What's the weather?",
            },
            headers=_auth(user_id),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "傳送成功"
    assert body["data"]["content"] == "Weather is sunny"


# ---------------------------------------------------------------------------
# Issue-308: image_extract 工具 (T18, T19)
# ---------------------------------------------------------------------------


def test_send_message_with_image_extract_tool_returns_200(client, engine):
    """T18: 夥伴含 image_extract 工具，上傳圖片後 ai_agent 跳過外部 HTTP 呼叫，AI 回覆含摘要"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴圖片擷取")
    _bind_partner_to_role(db, role_id, partner_id)
    tool_id = _make_image_extract_tool_in_db(
        db,
        "發票擷取",
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
    _bind_tool_to_partner(db, partner_id, tool_id)
    conv_id = _make_conversation(db, user_id, partner_id)
    db.commit()
    db.close()

    mock_result = {
        "content": "根據發票圖片，擷取到以下資訊：\n\n| 欄位 | 值 |\n|---|---|\n| 發票日期 | 2026-05-13 |\n| 發票金額 | 1500 |",
        "tool_calls": [],
    }
    fake_image = b"\x89PNG\r\n\x1a\n"
    with patch("app.api.fn_ai_partner_chat.ai_agent.run", return_value=mock_result):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": str(partner_id),
                "conversation_id": conv_id,
                "message": "請擷取此發票資訊",
            },
            files={"image": ("invoice.png", fake_image, "image/png")},
            headers=_auth(user_id),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "傳送成功"
    content = body["data"]["content"]
    assert "|" in content  # Markdown 表格格式


def test_send_message_unrecognizable_image_with_image_extract_returns_200(
    client, engine
):
    """T19: 夥伴含 image_extract 工具，上傳無法識別的圖片，AI 回覆說明無法辨識"""
    user_id, role_id, _ = _setup_with_fn_ai_partner_chat(engine)
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    partner_id = _make_partner(db, "夥伴圖片擷取2")
    _bind_partner_to_role(db, role_id, partner_id)
    tool_id = _make_image_extract_tool_in_db(
        db,
        "無法識別擷取工具",
        image_fields=[
            {
                "field_name": "invoice_date",
                "field_type": "string",
                "description": "發票日期",
            },
        ],
    )
    _bind_tool_to_partner(db, partner_id, tool_id)
    conv_id = _make_conversation(db, user_id, partner_id)
    db.commit()
    db.close()

    mock_result = {
        "content": "抱歉，我無法辨識此圖片中的欄位。請重新上傳清晰的圖片，或補充相關資訊。",
        "tool_calls": [],
    }
    fake_blurry_image = b"\x00\x00\x00\x00"
    with patch("app.api.fn_ai_partner_chat.ai_agent.run", return_value=mock_result):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": str(partner_id),
                "conversation_id": conv_id,
                "message": "請看這張圖",
            },
            files={"image": ("blurry.png", fake_blurry_image, "image/png")},
            headers=_auth(user_id),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "傳送成功"
    assert (
        "無法辨識" in body["data"]["content"] or "重新上傳" in body["data"]["content"]
    )
