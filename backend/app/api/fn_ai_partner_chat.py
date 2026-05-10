"""/api/ai-partner-chat router — AI 夥伴對話 (fn_ai_partner_chat)."""

import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.schema.fn_ai_partner_chat import (
    HistoryData,
    HistoryOut,
    MessageItem,
    NewData,
    NewOut,
    NewRequest,
    OptionsOut,
    PartnerItem,
    PartnerOptionItem,
    PartnersOut,
    SendData,
    SendOut,
)
from app.config.settings import settings
from app.db.connector import get_db
from app.db.models.fn_ai_partner_chat import Conversation, Message, RoleAiPartner
from app.db.models.fn_ai_partner_config import AiPartnerConfig, AiPartnerTool
from app.db.models.fn_tool import Tool, ToolBodyParam
from app.db.models.function_access import FunctionItems, RoleFunction
from app.db.models.user_role import UserRole
from app.logger_utils import get_system_logger
from app.services import ai_agent
from app.services.ai_agent import AgentMaxIterationError
from app.services.llm_client import LLMClientError
from app.utils.util_store import AuthContext, authenticate

router = APIRouter(prefix="/ai-partner-chat", tags=["fn_ai_partner_chat"])
system_logger = get_system_logger()

FN_AI_PARTNER_CHAT_CODE = "fn_ai_partner_chat"


# ── Permission helpers ───────────────────────────────────────────────────────


def _has_fn_permission(user_id: int, function_code: str, db: Session) -> bool:
    """Return True if the user has the given function permission."""
    fn = (
        db.query(FunctionItems)
        .filter(FunctionItems.function_code == function_code)
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


def _get_role_ids(user_id: int, db: Session) -> list[int]:
    """Return list of role_ids for the user."""
    rows = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    return [r.role_id for r in rows]


def _can_use_partner(user_id: int, partner_id: int, db: Session) -> bool:
    """Return True if any of the user's roles is bound to the given partner and partner is enabled."""
    role_ids = _get_role_ids(user_id, db)
    if not role_ids:
        return False
    partner = (
        db.query(AiPartnerConfig)
        .filter(AiPartnerConfig.id == partner_id, AiPartnerConfig.is_enabled.is_(True))
        .first()
    )
    if partner is None:
        return False
    binding = (
        db.query(RoleAiPartner)
        .filter(
            RoleAiPartner.role_id.in_(role_ids),
            RoleAiPartner.partner_id == partner_id,
        )
        .first()
    )
    return binding is not None


# ── System prompt assembly ────────────────────────────────────────────────────


def _build_system_prompt(partner: AiPartnerConfig) -> str:
    """組裝 system prompt：{role_definition}\n\n限制事項：\n{behavior_limit}。"""
    parts = []
    if partner.role_definition:
        parts.append(partner.role_definition)
    if partner.behavior_limit:
        if parts:
            parts.append("\n\n限制事項：\n" + partner.behavior_limit)
        else:
            parts.append("限制事項：\n" + partner.behavior_limit)
    return "".join(parts)


# ── Tool definition assembly ──────────────────────────────────────────────────


def _build_tool_definitions(
    partner_id: int, db: Session
) -> tuple[list[dict], list[dict]]:
    """從 tb_ai_partner_tools JOIN tb_tools + tb_tool_body_params 組裝 tool 定義與設定清單。

    Returns:
        (tool_defs, tool_configs) — Anthropic format defs & execution configs.
    """
    tool_rows = (
        db.query(Tool)
        .join(AiPartnerTool, Tool.id == AiPartnerTool.tool_id)
        .filter(AiPartnerTool.partner_id == partner_id)
        .all()
    )

    tool_defs: list[dict] = []
    tool_configs: list[dict] = []

    for tool in tool_rows:
        params = (
            db.query(ToolBodyParam)
            .filter(ToolBodyParam.tool_id == tool.id)
            .order_by(ToolBodyParam.sort_order.asc())
            .all()
        )

        # Anthropic tool definition
        properties: dict = {}
        required_params: list[str] = []
        for p in params:
            type_map = {
                "string": "string",
                "number": "number",
                "boolean": "boolean",
                "object": "object",
            }
            properties[p.param_name] = {
                "type": type_map.get(p.param_type, "string"),
                "description": p.description or "",
            }
            if p.is_required:
                required_params.append(p.param_name)

        tool_defs.append(
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required_params,
                },
            }
        )

        # Execution config
        tool_configs.append(
            {
                "name": tool.name,
                "endpoint_url": tool.endpoint_url,
                "http_method": tool.http_method,
                "auth_type": tool.auth_type,
                "auth_header_name": tool.auth_header_name,
                "credential": tool.credential_enc or "",
            }
        )

    return tool_defs, tool_configs


# ── Conversation history helpers ──────────────────────────────────────────────


def _build_context_messages(conversation_id: str, db: Session) -> list[dict]:
    """取最近 20 輪對話歷史（每輪含 user + assistant）作為 context。"""
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(40)  # 最多取 40 筆（約 20 輪）
        .all()
    )
    msgs = list(reversed(msgs))
    return [{"role": m.role, "content": m.content} for m in msgs]


# ── Suggestions parsing ───────────────────────────────────────────────────────


def _parse_suggestions(tool_calls: list[dict]) -> list[str]:
    """從 tool_use 結果解析 suggestions（字串陣列）。"""
    for tc in tool_calls:
        inp = tc.get("input", {})
        if "suggestions" in inp:
            suggestions = inp["suggestions"]
            if isinstance(suggestions, list):
                return [str(s) for s in suggestions]
    return []


# ── GET /api/ai-partner-chat/partners ────────────────────────────────────────


@router.get("/partners", response_model=PartnersOut)
def list_partners(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> PartnersOut:
    """取得當前角色可用的 AI 夥伴清單。"""
    if not _has_fn_permission(auth.user_id, FN_AI_PARTNER_CHAT_CODE, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    role_ids = _get_role_ids(auth.user_id, db)
    if not role_ids:
        return PartnersOut(data=[])

    partners = (
        db.query(AiPartnerConfig)
        .join(RoleAiPartner, AiPartnerConfig.id == RoleAiPartner.partner_id)
        .filter(
            RoleAiPartner.role_id.in_(role_ids),
            AiPartnerConfig.is_enabled.is_(True),
        )
        .distinct()
        .all()
    )

    items = [
        PartnerItem(id=p.id, name=p.name, description=p.description) for p in partners
    ]
    return PartnersOut(data=items)


# ── GET /api/ai-partner-chat/history ─────────────────────────────────────────


@router.get("/history", response_model=HistoryOut)
def get_history(
    partner_id: int = Query(..., description="AI 夥伴 ID"),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> HistoryOut:
    """取得指定夥伴的最新一筆會話歷史。"""
    if not _has_fn_permission(auth.user_id, FN_AI_PARTNER_CHAT_CODE, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    if not _can_use_partner(auth.user_id, partner_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有使用此 AI 夥伴的權限",
        )

    # 取最新一筆 conversation
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == auth.user_id,
            Conversation.partner_id == partner_id,
        )
        .order_by(Conversation.created_at.desc())
        .first()
    )

    if conversation is None:
        return HistoryOut(
            data=HistoryData(
                conversation_id=None,
                messages=[],
                suggestions=[],
            )
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    message_items = [
        MessageItem(
            role=m.role,
            content=m.content,
            image_url=m.image_url,
            created_at=m.created_at,
        )
        for m in messages
    ]

    suggestions = conversation.latest_suggestions or []

    return HistoryOut(
        data=HistoryData(
            conversation_id=conversation.id,
            messages=message_items,
            suggestions=suggestions,
        )
    )


# ── POST /api/ai-partner-chat/send ───────────────────────────────────────────


@router.post("/send", response_model=SendOut)
def send_message(
    partner_id: int = Form(...),
    conversation_id: str = Form(...),
    message: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> SendOut:
    """送出訊息並取得 AI 回覆。"""
    if not _has_fn_permission(auth.user_id, FN_AI_PARTNER_CHAT_CODE, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    if not _can_use_partner(auth.user_id, partner_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有使用此 AI 夥伴的權限",
        )

    # 確認 conversation 屬於當前使用者與指定夥伴
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == auth.user_id,
            Conversation.partner_id == partner_id,
        )
        .first()
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有使用此 AI 夥伴的權限",
        )

    # 訊息內容不可為空
    has_message = bool(message and message.strip())
    has_image = image is not None
    if not has_message and not has_image:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="訊息內容不可為空",
        )

    # 讀取 partner 設定
    partner = db.query(AiPartnerConfig).filter(AiPartnerConfig.id == partner_id).first()
    system_prompt = _build_system_prompt(partner)

    # 寫入使用者訊息
    user_content = message.strip() if has_message else ""
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=user_content,
        image_url=None,  # 暫存 NULL，待 R2 整合
    )
    db.add(user_msg)
    db.flush()

    # 組裝對話歷史 context（最近 20 輪，不含剛寫入的 user_msg）
    history_msgs = _build_context_messages(conversation_id, db)

    # 若有圖片，以 vision 格式納入當輪 user message
    if has_image:
        image_bytes = image.file.read()
        import base64

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        media_type = image.content_type or "image/jpeg"
        user_vision_content: list = []
        if has_message:
            user_vision_content.append({"type": "text", "text": user_content})
        user_vision_content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_b64,
                },
            }
        )
        # 附加帶圖片的當輪訊息
        history_msgs.append({"role": "user", "content": user_vision_content})
    else:
        history_msgs.append({"role": "user", "content": user_content})

    # 組裝工具定義
    tool_defs, tool_configs = _build_tool_definitions(partner_id, db)
    model = partner.model_name or settings.anthropic_model

    try:
        result = ai_agent.run(
            model=model,
            system=system_prompt,
            messages=history_msgs,
            tools=tool_defs or None,
            tool_configs=tool_configs or None,
        )
    except (AgentMaxIterationError, LLMClientError):  # fmt: skip
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI 服務暫時無法使用",
        )

    ai_content = result.get("content", "")
    suggestions = _parse_suggestions(result.get("tool_calls", []))

    # 寫入 AI 回覆
    ai_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_content,
        image_url=None,
    )
    db.add(ai_msg)

    # 更新 latest_suggestions
    conversation.latest_suggestions = suggestions if suggestions else None

    db.commit()
    system_logger.info(
        f"User {auth.user_id} sent message to partner {partner_id}, conv {conversation_id}"
    )

    return SendOut(data=SendData(content=ai_content, suggestions=suggestions))


# ── POST /api/ai-partner-chat/new ────────────────────────────────────────────


@router.post("/new", response_model=NewOut, status_code=status.HTTP_201_CREATED)
def new_conversation(
    payload: NewRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> NewOut:
    """開始新對話，建立新 conversation_id，產生 AI 開場問候。"""
    if not _has_fn_permission(auth.user_id, FN_AI_PARTNER_CHAT_CODE, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有執行此操作的權限",
        )

    if not _can_use_partner(auth.user_id, payload.partner_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您沒有使用此 AI 夥伴的權限",
        )

    # 建立新 conversation（舊有紀錄保留不刪除）
    new_conv_id = str(uuid.uuid4())
    conversation = Conversation(
        id=new_conv_id,
        user_id=auth.user_id,
        partner_id=payload.partner_id,
        latest_suggestions=None,
    )
    db.add(conversation)
    db.flush()

    # 讀取 partner 設定
    partner = (
        db.query(AiPartnerConfig)
        .filter(AiPartnerConfig.id == payload.partner_id)
        .first()
    )
    system_prompt = _build_system_prompt(partner)
    model = partner.model_name or settings.anthropic_model

    # 組裝工具定義（含 suggestions tool）
    tool_defs, tool_configs = _build_tool_definitions(payload.partner_id, db)

    # 加入一個內建 suggestions tool 以取得初始 suggestions
    greeting_tool = {
        "name": "provide_greeting_and_suggestions",
        "description": "提供開場問候與初始建議問題",
        "input_schema": {
            "type": "object",
            "properties": {
                "greeting": {"type": "string", "description": "AI 開場問候訊息"},
                "suggestions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "初始建議問題陣列（3-5 條）",
                },
            },
            "required": ["greeting", "suggestions"],
        },
    }
    greeting_tools = [greeting_tool] + tool_defs

    # 產生開場問候的 prompt
    greeting_messages = [
        {
            "role": "user",
            "content": "請使用 provide_greeting_and_suggestions tool 提供開場問候（含自我介紹、可協助項目、互動提示範例）與初始建議問題。",
        }
    ]

    try:
        result = ai_agent.run(
            model=model,
            system=system_prompt,
            messages=greeting_messages,
            tools=greeting_tools,
            tool_configs=tool_configs or None,
        )
    except (AgentMaxIterationError, LLMClientError):  # fmt: skip
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI 服務暫時無法使用",
        )

    # 解析問候與 suggestions
    greeting_content = result.get("content", "")
    suggestions: list[str] = []
    for tc in result.get("tool_calls", []):
        if tc.get("name") == "provide_greeting_and_suggestions":
            inp = tc.get("input", {})
            greeting_content = inp.get("greeting", greeting_content)
            suggestions = inp.get("suggestions", [])
            if isinstance(suggestions, list):
                suggestions = [str(s) for s in suggestions]
            break

    # 若未取得 greeting_content，用 content 回退
    if not greeting_content:
        greeting_content = "您好！我是您的 AI 夥伴，很高興認識您。"

    # 寫入開場問候訊息
    ai_msg = Message(
        conversation_id=new_conv_id,
        role="assistant",
        content=greeting_content,
        image_url=None,
    )
    db.add(ai_msg)
    db.flush()

    # 更新 latest_suggestions
    conversation.latest_suggestions = suggestions if suggestions else None

    db.commit()
    system_logger.info(
        f"User {auth.user_id} created new conversation {new_conv_id} with partner {payload.partner_id}"
    )

    message_items = [
        MessageItem(
            role=ai_msg.role,
            content=ai_msg.content,
            image_url=ai_msg.image_url,
            created_at=ai_msg.created_at,
        )
    ]

    return NewOut(
        data=NewData(
            conversation_id=new_conv_id,
            messages=message_items,
            suggestions=suggestions,
        )
    )


# ── GET /api/ai-partner-chat/options ─────────────────────────────────────────


@router.get("/options", response_model=OptionsOut)
def list_options(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(authenticate),
) -> OptionsOut:
    """取得系統中所有啟用中 AI 夥伴選項，依名稱升冪排序。"""
    partners = (
        db.query(AiPartnerConfig)
        .filter(AiPartnerConfig.is_enabled.is_(True))
        .order_by(AiPartnerConfig.name.asc())
        .all()
    )
    items = [PartnerOptionItem(id=p.id, name=p.name) for p in partners]
    return OptionsOut(data=items)
