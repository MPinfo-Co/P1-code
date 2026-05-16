"""
Tests for fn_ai_partner_chat send API with cross-table relations injection.

對應測試案例 T26–T30（fn_ai_partner_chat）
"""

import uuid
from unittest.mock import patch

from sqlalchemy.orm import Session, sessionmaker

from app.db.models.fn_ai_partner_chat import Conversation, RoleAiPartner
from app.db.models.fn_ai_partner_config import AiPartnerConfig, AiPartnerTool
from app.db.models.fn_ai_partner_tool import Tool, ToolReadCustomTableConfig
from app.db.models.fn_custom_table import (
    CustomTable,
    CustomTableField,
    CustomTableRelation,
)
from app.db.models.function_access import FunctionFolder, FunctionItems, RoleFunction
from app.db.models.user_role import Role, User, UserRole
from app.utils.util_store import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _make_folder(db: Session, code: str, label: str = "AI 夥伴") -> int:
    f = FunctionFolder(folder_code=code, folder_label=label, sort_order=1)
    db.add(f)
    db.flush()
    return f.id


def _make_function(db: Session, code: str, folder_id: int) -> int:
    fn = FunctionItems(
        function_code=code,
        function_label=code,
        folder_id=folder_id,
        sort_order=1,
    )
    db.add(fn)
    db.flush()
    return fn.function_id


def _make_role(db: Session, name: str) -> int:
    r = Role(name=name)
    db.add(r)
    db.flush()
    return r.id


def _make_user(db: Session, email: str) -> int:
    u = User(name="Test", email=email, password_hash=hash_password("pw"))
    db.add(u)
    db.flush()
    return u.id


def _assign_role(db: Session, user_id: int, role_id: int) -> None:
    db.add(UserRole(user_id=user_id, role_id=role_id))
    db.flush()


def _grant_fn(db: Session, role_id: int, fn_id: int) -> None:
    db.add(RoleFunction(role_id=role_id, function_id=fn_id))
    db.flush()


def _make_partner(db: Session, name: str) -> int:
    p = AiPartnerConfig(
        name=name,
        description=f"描述: {name}",
        is_enabled=True,
        role_definition="你是一個助手",
        behavior_limit=None,
    )
    db.add(p)
    db.flush()
    return p.id


def _bind_partner(db: Session, role_id: int, partner_id: int) -> None:
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


def _make_custom_table(db: Session, name: str, fields: list[str]) -> int:
    """Create a custom table with named fields. Return table id."""
    tbl = CustomTable(name=name)
    db.add(tbl)
    db.flush()
    for i, field_name in enumerate(fields):
        db.add(
            CustomTableField(
                table_id=tbl.id,
                field_name=field_name,
                field_type="string",
                sort_order=i,
            )
        )
    return tbl.id


def _attach_read_tool(
    db: Session, partner_id: int, table_id: int, tool_name: str
) -> int:
    """Create a read_custom_table tool and attach to partner. Return tool id."""
    tool = Tool(name=tool_name, tool_type="read_custom_table", auth_type="none")
    db.add(tool)
    db.flush()
    db.add(
        ToolReadCustomTableConfig(
            tool_id=tool.id,
            target_table_id=table_id,
            limit=20,
            scope="all",
        )
    )
    db.add(AiPartnerTool(partner_id=partner_id, tool_id=tool.id))
    db.flush()
    return tool.id


def _setup_user_with_chat_permission(engine, suffix: str) -> tuple[int, int]:
    """Return (user_id, role_id)."""
    Session_ = sessionmaker(bind=engine)
    db = Session_()
    folder_id = _make_folder(db, f"ai_folder_{suffix}")
    fn_id = _make_function(db, "fn_ai_partner_chat", folder_id)
    role_id = _make_role(db, f"chat_role_{suffix}")
    user_id = _make_user(db, f"chat_{suffix}@test.com")
    _assign_role(db, user_id, role_id)
    _grant_fn(db, role_id, fn_id)
    db.commit()
    db.close()
    return user_id, role_id


# ---------------------------------------------------------------------------
# T26: POST /ai-partner-chat/send — 有 read_custom_table 工具且有關聯 → system prompt 含關聯說明
# ---------------------------------------------------------------------------


def test_send_message_with_relations_injects_prompt(client, engine):
    """對應 T26：夥伴掛載 2 個 read_custom_table 工具，DB 有 1 筆關聯
    → 200；system prompt 已包含關聯說明"""
    user_id, role_id = _setup_user_with_chat_permission(engine, "t26")

    Session_ = sessionmaker(bind=engine)
    db = Session_()

    partner_id = _make_partner(db, "跨表夥伴T26")
    _bind_partner(db, role_id, partner_id)
    conv_id = _make_conversation(db, user_id, partner_id)

    order_table_id = _make_custom_table(db, "訂單表T26", ["客戶ID", "金額"])
    customer_table_id = _make_custom_table(db, "客戶表T26", ["id", "姓名"])
    _attach_read_tool(db, partner_id, order_table_id, "讀訂單T26")
    _attach_read_tool(db, partner_id, customer_table_id, "讀客戶T26")

    # 建立關聯
    db.add(
        CustomTableRelation(
            src_table_id=order_table_id,
            src_field="客戶ID",
            dst_table_id=customer_table_id,
            dst_field="id",
        )
    )
    db.commit()
    db.close()

    captured_system: list[str] = []

    def _mock_run(model, system, messages, tools, tool_configs, db):
        captured_system.append(system)
        return {"content": "跨表分析結果", "chart_data": None}

    with patch("app.api.fn_ai_partner_chat.ai_agent.run", side_effect=_mock_run):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": str(partner_id),
                "conversation_id": conv_id,
                "message": "本月哪些客戶下單超過 3 次？",
            },
            headers=_auth(user_id),
        )

    assert resp.status_code == 200
    assert resp.json()["message"] == "傳送成功"
    assert len(captured_system) == 1
    system_prompt_used = captured_system[0]
    assert "以下是資料表之間已定義的欄位關聯" in system_prompt_used
    assert "訂單表T26.客戶ID" in system_prompt_used
    assert "客戶表T26.id" in system_prompt_used


# ---------------------------------------------------------------------------
# T27: POST /ai-partner-chat/send — 有 read_custom_table 但 DB 無關聯 → 不注入
# ---------------------------------------------------------------------------


def test_send_message_with_read_tool_no_relations_no_injection(client, engine):
    """對應 T27：夥伴掛載 1 個 read_custom_table 工具，DB 無任何關聯
    → 200；system prompt 不含關聯說明"""
    user_id, role_id = _setup_user_with_chat_permission(engine, "t27")

    Session_ = sessionmaker(bind=engine)
    db = Session_()

    partner_id = _make_partner(db, "空關聯夥伴T27")
    _bind_partner(db, role_id, partner_id)
    conv_id = _make_conversation(db, user_id, partner_id)

    table_id = _make_custom_table(db, "訂單表T27", ["欄位A"])
    _attach_read_tool(db, partner_id, table_id, "讀訂單T27")

    db.commit()
    db.close()

    captured_system: list[str] = []

    def _mock_run(model, system, messages, tools, tool_configs, db):
        captured_system.append(system)
        return {"content": "一般回覆", "chart_data": None}

    with patch("app.api.fn_ai_partner_chat.ai_agent.run", side_effect=_mock_run):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": str(partner_id),
                "conversation_id": conv_id,
                "message": "一般問答",
            },
            headers=_auth(user_id),
        )

    assert resp.status_code == 200
    assert resp.json()["message"] == "傳送成功"
    assert len(captured_system) == 1
    system_prompt_used = captured_system[0]
    assert "以下是資料表之間已定義的欄位關聯" not in system_prompt_used


# ---------------------------------------------------------------------------
# T28: POST /ai-partner-chat/send — 無 read_custom_table 工具，有關聯 → 不注入
# ---------------------------------------------------------------------------


def test_send_message_no_read_tool_skips_relations_injection(client, engine):
    """對應 T28：夥伴未掛載 read_custom_table 工具，DB 有 3 筆關聯
    → 200；system prompt 不注入關聯圖"""
    user_id, role_id = _setup_user_with_chat_permission(engine, "t28")

    Session_ = sessionmaker(bind=engine)
    db = Session_()

    partner_id = _make_partner(db, "無讀工具夥伴T28")
    _bind_partner(db, role_id, partner_id)
    conv_id = _make_conversation(db, user_id, partner_id)

    # 建立 3 筆關聯（但夥伴未掛載 read_custom_table 工具）
    tbl1 = _make_custom_table(db, "表一T28", ["欄A"])
    tbl2 = _make_custom_table(db, "表二T28", ["欄B"])
    for i in range(3):
        db.add(
            CustomTableRelation(
                src_table_id=tbl1,
                src_field=f"欄{i}",
                dst_table_id=tbl2,
                dst_field=f"目{i}",
            )
        )
    db.commit()
    db.close()

    captured_system: list[str] = []

    def _mock_run(model, system, messages, tools, tool_configs, db):
        captured_system.append(system)
        return {"content": "正常回覆", "chart_data": None}

    with patch("app.api.fn_ai_partner_chat.ai_agent.run", side_effect=_mock_run):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": str(partner_id),
                "conversation_id": conv_id,
                "message": "一般問答",
            },
            headers=_auth(user_id),
        )

    assert resp.status_code == 200
    assert resp.json()["message"] == "傳送成功"
    assert len(captured_system) == 1
    system_prompt_used = captured_system[0]
    assert "以下是資料表之間已定義的欄位關聯" not in system_prompt_used


# ---------------------------------------------------------------------------
# T29: POST /ai-partner-chat/send — 未登入 → 401
# ---------------------------------------------------------------------------


def test_send_message_unauthenticated_returns_401(client, engine):
    """對應 T29：未登入 → 401 未登入或 Token 過期"""
    resp = client.post(
        "/ai-partner-chat/send",
        data={
            "partner_id": "1",
            "conversation_id": "some-conv-id",
            "message": "你好",
        },
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# T30: POST /ai-partner-chat/send — 關聯只注入夥伴可存取兩端的關聯
# ---------------------------------------------------------------------------


def test_send_message_relations_only_accessible_tables(client, engine):
    """對應 T30：夥伴掛載多個 read_custom_table 工具，DB 有對應關聯定義
    → 200；system prompt 已注入關聯圖（只含夥伴可存取的兩端關聯）"""
    user_id, role_id = _setup_user_with_chat_permission(engine, "t30")

    Session_ = sessionmaker(bind=engine)
    db = Session_()

    partner_id = _make_partner(db, "多工具夥伴T30")
    _bind_partner(db, role_id, partner_id)
    conv_id = _make_conversation(db, user_id, partner_id)

    # 夥伴可存取的三個表
    order_table_id = _make_custom_table(db, "訂單表T30", ["客戶ID"])
    stock_table_id = _make_custom_table(db, "庫存表T30", ["商品ID"])
    complaint_table_id = _make_custom_table(db, "客訴表T30", ["客戶ID"])

    # 額外一個夥伴「無法存取」的表
    other_table_id = _make_custom_table(db, "其他表T30", ["欄位X"])

    _attach_read_tool(db, partner_id, order_table_id, "讀訂單T30")
    _attach_read_tool(db, partner_id, stock_table_id, "讀庫存T30")
    _attach_read_tool(db, partner_id, complaint_table_id, "讀客訴T30")

    # 建立兩端皆可存取的關聯
    db.add(
        CustomTableRelation(
            src_table_id=order_table_id,
            src_field="客戶ID",
            dst_table_id=complaint_table_id,
            dst_field="客戶ID",
        )
    )
    # 建立一端不可存取的關聯（應被過濾掉）
    db.add(
        CustomTableRelation(
            src_table_id=order_table_id,
            src_field="客戶ID",
            dst_table_id=other_table_id,
            dst_field="欄位X",
        )
    )
    db.commit()
    db.close()

    captured_system: list[str] = []

    def _mock_run(model, system, messages, tools, tool_configs, db):
        captured_system.append(system)
        return {"content": "洞見摘要回覆", "chart_data": None}

    with patch("app.api.fn_ai_partner_chat.ai_agent.run", side_effect=_mock_run):
        resp = client.post(
            "/ai-partner-chat/send",
            data={
                "partner_id": str(partner_id),
                "conversation_id": conv_id,
                "message": "今天有什麼我不知道的異常？",
            },
            headers=_auth(user_id),
        )

    assert resp.status_code == 200
    assert resp.json()["message"] == "傳送成功"
    assert len(captured_system) == 1
    system_prompt_used = captured_system[0]

    # 夥伴可存取兩端的關聯應被注入
    assert "以下是資料表之間已定義的欄位關聯" in system_prompt_used
    assert "訂單表T30.客戶ID" in system_prompt_used
    assert "客訴表T30.客戶ID" in system_prompt_used

    # 不可存取的表（其他表T30）不應被注入
    assert "其他表T30" not in system_prompt_used
