"""AI Agent — 執行 agentic loop。

職責：
- 呼叫 llm_client.chat()
- 判斷 tool_call，執行外部工具 API（external_api / image_extract / web_scraper / write_custom_table / read_custom_table）
- 帶回 tool_result 繼續對話
- 迴圈上限 5 次，超過則 raise AgentMaxIterationError
- URL 樣板替換（{xxx} → tool input 參數值）
- 工具名稱正規化（中文及非法字元 → Anthropic 合法格式）
"""

import json
import re
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.services.llm_client import LLMClientError, chat  # noqa: F401 (re-export for convenience)


class AgentMaxIterationError(Exception):
    """agentic loop 達到迴圈上限（5 次），上層捕捉後回傳 503。"""


def _normalize_property_keys(
    tools: list[dict],
) -> tuple[list[dict], dict[str, dict[str, str]]]:
    """對每個工具的 input_schema.properties 執行 key 正規化。

    Anthropic 要求 properties key 符合 ^[a-zA-Z0-9_.-]{1,64}$，中文或含空格的
    欄位名稱必須轉換。轉換後的 safe_key 以 f_{i} 命名，原始名稱合併至 description
    讓 LLM 仍能理解語意。

    Args:
        tools: 已完成 name 正規化的工具定義清單。

    Returns:
        (normalized_tools, prop_mapping)
        - normalized_tools: properties key 已替換的工具定義清單。
        - prop_mapping: {tool_name: {safe_key: original_key}} 還原用映射表。
    """
    prop_mapping: dict[str, dict[str, str]] = {}
    normalized: list[dict] = []

    for tool in tools:
        tool_name: str = tool["name"]
        schema: dict = tool.get("input_schema", {})
        props: dict = schema.get("properties", {})
        required: list = schema.get("required", [])

        key_map: dict[str, str] = {}
        new_props: dict = {}
        new_required: list = []

        for i, (orig_key, prop_def) in enumerate(props.items()):
            if re.match(r"^[a-zA-Z0-9_.\-]{1,64}$", orig_key):
                safe_key = orig_key
            else:
                safe_key = f"f_{i}"
                prop_def = dict(prop_def)
                existing_desc = prop_def.get("description", "")
                prop_def["description"] = (
                    f"{orig_key}：{existing_desc}" if existing_desc else orig_key
                )

            key_map[safe_key] = orig_key
            new_props[safe_key] = prop_def
            if orig_key in required:
                new_required.append(safe_key)

        new_tool = dict(tool)
        new_tool["input_schema"] = {
            **schema,
            "properties": new_props,
            "required": new_required,
        }
        normalized.append(new_tool)

        if any(k != v for k, v in key_map.items()):
            prop_mapping[tool_name] = key_map

    return normalized, prop_mapping


def _normalize_tool_names(
    tools: list[dict],
) -> tuple[list[dict], dict[str, str]]:
    """對工具定義清單中每個工具的 name 欄位執行正規化。

    Anthropic API 要求工具 name 只能包含 a-z A-Z 0-9 _ -。
    tb_tools.name 允許中文及任意字元，因此需在組裝工具定義清單時進行轉換。

    轉換規則：
    1. 以 _ 替換所有非 a-z A-Z 0-9 _ - 字元（含中文、空白、特殊符號）。
    2. 若替換後開頭為數字或 _ / -，前綴 tool_。
    3. 若轉換後與已有名稱重複，改用 tool_{index}（index 從 0 起，依工具清單順序遞增）。
    4. 最終合法名稱須符合：^[a-zA-Z][a-zA-Z0-9_-]*$

    Args:
        tools: Anthropic tool_use 格式的工具定義清單（含原始 name）。

    Returns:
        (normalized_tools, name_mapping)
        - normalized_tools: name 已替換為合法名稱的工具定義清單。
        - name_mapping: 正規化後名稱 → 原始名稱 的對映表。
    """
    name_mapping: dict[str, str] = {}
    normalized_tools: list[dict] = []
    used_names: set[str] = set()

    for idx, tool in enumerate(tools):
        original_name: str = tool["name"]

        # 步驟1：以 _ 替換非法字元
        candidate = re.sub(r"[^a-zA-Z0-9_\-]", "_", original_name)

        # 步驟2：若開頭為數字、_ 或 -，前綴 tool_
        if candidate and re.match(r"^[0-9_\-]", candidate):
            candidate = "tool_" + candidate

        # 步驟3：若為空字串或仍不合法，或與已用名稱重複，改用 tool_{index}
        if (
            not candidate
            or not re.match(r"^[a-zA-Z][a-zA-Z0-9_\-]*$", candidate)
            or candidate in used_names
        ):
            candidate = f"tool_{idx}"

        used_names.add(candidate)
        name_mapping[candidate] = original_name

        normalized_tool = dict(tool)
        normalized_tool["name"] = candidate
        normalized_tools.append(normalized_tool)

    return normalized_tools, name_mapping


def run(
    model: str,
    system: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    tool_configs: list[dict] | None = None,
    db: Session | None = None,
) -> dict:
    """執行完整 agentic loop，回傳最終 AI 回覆與 tool_use 結果。

    Args:
        model: 模型名稱。
        system: 組裝完成的 system prompt。
        messages: 對話歷史（含本輪 user message）。
        tools: Anthropic tool_use 格式的工具定義清單；無工具時傳 None。
        tool_configs: 對應 tools 的執行設定（tool_type, endpoint_url, http_method, auth_type 等）；
                      無工具時傳 None。
        db: SQLAlchemy Session，write_custom_table / read_custom_table 工具執行時需要。

    Returns:
        dict: {
            "content": str,           # AI 最終回覆文字
            "tool_calls": list[dict]  # 最後一輪的 tool_use 結果；無時為空陣列
        }

    Raises:
        AgentMaxIterationError: tool_call 迴圈達到上限（5 次）。
        LLMClientError: LLM 呼叫失敗，直接向上傳遞。
    """
    MAX_ITERATIONS = 5
    iteration = 0
    current_messages = list(messages)

    # 工具名稱正規化：建立 normalized_tools 及 正規化後名稱 → 原始名稱 對映表
    prop_key_mapping: dict[str, dict[str, str]] = {}
    if tools:
        normalized_tools, name_mapping = _normalize_tool_names(tools)
        normalized_tools, prop_key_mapping = _normalize_property_keys(normalized_tools)
    else:
        normalized_tools = tools
        name_mapping: dict[str, str] = {}

    while True:
        result = chat(
            model=model,
            system=system,
            messages=current_messages,
            tools=normalized_tools,
        )

        tool_calls = result.get("tool_calls", [])

        # 無 tool_call → 對話結束，回傳最終結果
        if not tool_calls:
            return result

        # 有 tool_call → 還原正規化名稱為原始名稱，再執行外部工具
        iteration += 1
        if iteration >= MAX_ITERATIONS:
            raise AgentMaxIterationError(
                f"agentic loop 達到迴圈上限（{MAX_ITERATIONS} 次）"
            )

        # 還原 tool_calls 中的正規化名稱為原始名稱（供 _execute_tool 查找 tool_configs）
        restored_tool_calls = []
        for tc in tool_calls:
            normalized_name = tc["name"]
            original_name = name_mapping.get(normalized_name, normalized_name)
            restored_tc = dict(tc)
            restored_tc["name"] = original_name
            restored_tool_calls.append(restored_tc)

        # 將 assistant 的 tool_use 回應附加到 messages
        # Anthropic 格式：assistant message 的 content 為 block 陣列
        # 注意：傳給 Anthropic 的 name 須使用正規化後名稱
        assistant_content = []
        if result.get("content"):
            assistant_content.append({"type": "text", "text": result["content"]})
        for tc in tool_calls:
            assistant_content.append(
                {
                    "type": "tool_use",
                    "id": tc["id"],
                    "name": tc["name"],
                    "input": tc["input"],
                }
            )
        current_messages.append({"role": "assistant", "content": assistant_content})

        # 執行每個 tool_call（使用還原後的原始名稱查找 tool_configs）
        tool_results = []
        for tc in restored_tool_calls:
            tool_result_content = _execute_tool(
                tc, tool_configs or [], prop_key_mapping, db=db
            )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": tool_result_content,
                }
            )

        # 將 tool_result 附加到 messages（user role）
        current_messages.append({"role": "user", "content": tool_results})


def _execute_tool(
    tool_call: dict,
    tool_configs: list[dict],
    prop_key_mapping: dict[str, dict[str, str]] | None = None,
    db: Session | None = None,
) -> str:
    """執行單一工具呼叫，回傳結果字串。

    Args:
        tool_call: {"id": ..., "name": ..., "input": {...}}
        tool_configs: 工具執行設定清單（來自 tb_tools + 各子表）
        prop_key_mapping: 屬性 key 正規化映射表
        db: SQLAlchemy Session，write/read_custom_table 工具需要

    Returns:
        str: 工具執行結果（或錯誤訊息）
    """
    tool_name = tool_call["name"]
    tool_input = tool_call.get("input", {})

    # 找對應的 tool_config
    config = next((c for c in tool_configs if c.get("name") == tool_name), None)
    if config is None:
        return f"[工具錯誤] 找不到工具設定：{tool_name}"

    # 判斷 tool_type
    tool_type: str = config.get("tool_type", "external_api")

    if tool_type == "image_extract":
        # image_extract：跳過外部 HTTP 呼叫
        # LLM 已在 vision 對話中看到圖片並自行填入 tool_input（結構化欄位值）
        # 還原 safe_key → 原始中文 key，再回傳
        key_map = (prop_key_mapping or {}).get(tool_name, {})
        remapped = {key_map.get(k, k): v for k, v in tool_input.items()}
        return json.dumps(remapped, ensure_ascii=False)

    if tool_type == "web_scraper":
        return _execute_web_scraper(config, tool_input)

    if tool_type == "write_custom_table":
        # 還原 safe_key → 原始欄位名稱（中文欄位名稱在正規化時被替換為 f_{i}）
        key_map = (prop_key_mapping or {}).get(tool_name, {})
        remapped_input = {key_map.get(k, k): v for k, v in tool_input.items()}
        return _execute_write_custom_table(config, remapped_input, db)

    if tool_type == "read_custom_table":
        return _execute_read_custom_table(config, db)

    # external_api：執行外部 HTTP 呼叫
    # URL 樣板替換
    endpoint_url: str = config.get("endpoint_url", "") or ""
    for key, value in tool_input.items():
        endpoint_url = endpoint_url.replace(f"{{{key}}}", quote(str(value), safe=""))

    http_method: str = (config.get("http_method", "GET") or "GET").upper()
    auth_type: str = config.get("auth_type", "none")
    auth_header_name: str = config.get("auth_header_name", "") or ""
    credential: str = config.get("credential", "") or ""

    headers: dict[str, str] = {}
    if auth_type == "api_key" and auth_header_name:
        headers[auth_header_name] = credential
    elif auth_type == "bearer":
        headers["Authorization"] = f"Bearer {credential}"

    try:
        with httpx.Client(timeout=30.0) as client:
            if http_method in ("GET", "DELETE"):
                resp = client.request(http_method, endpoint_url, headers=headers)
            else:
                resp = client.request(
                    http_method, endpoint_url, headers=headers, json=tool_input
                )
            return resp.text
    except Exception as exc:
        return f"[工具執行失敗] {exc}"


def _execute_write_custom_table(
    config: dict,
    tool_input: dict,
    db: Session | None,
) -> str:
    """執行 write_custom_table 類型工具呼叫。

    流程：
    1. 從 config 取 target_table_id 與 user_id（當前使用者）
    2. 依 tb_custom_table_fields 欄位定義，將 tool_input 轉換為 data JSONB
    3. INSERT 一筆 tb_custom_table_records，自動填入 updated_by=user_id
    """
    if db is None:
        return "[工具錯誤] write_custom_table 需要資料庫連線"

    from app.db.models.fn_custom_table import CustomTableField, CustomTableRecord

    target_table_id: int = config.get("target_table_id")
    user_id: int = config.get("user_id")

    if not target_table_id or not user_id:
        return "[工具錯誤] write_custom_table 設定不完整（缺少 target_table_id 或 user_id）"

    # 取欄位定義（確認有效欄位，供 AI tool_input 填值）
    fields = (
        db.query(CustomTableField)
        .filter(CustomTableField.table_id == target_table_id)
        .order_by(CustomTableField.sort_order.asc())
        .all()
    )

    # 將 tool_input 對應到欄位名稱（使用 field_name 作為 key）
    valid_field_names = {f.field_name for f in fields}
    data: dict = {k: v for k, v in tool_input.items() if k in valid_field_names}

    try:
        record = CustomTableRecord(
            table_id=target_table_id,
            data=data,
            updated_by=user_id,
        )
        db.add(record)
        db.commit()
        return json.dumps(
            {"success": True, "message": "資料已寫入"}, ensure_ascii=False
        )
    except Exception as exc:
        db.rollback()
        return f"[工具執行失敗] 寫入資料時發生錯誤：{exc}"


def _execute_read_custom_table(
    config: dict,
    db: Session | None,
) -> str:
    """執行 read_custom_table 類型工具呼叫。

    流程：
    1. 從 config 取 target_table_id、limit、scope、user_id
    2. 依 scope 過濾 tb_custom_table_records（self=只取當前使用者，all=全部）
    3. 排序 updated_at DESC，取前 limit 筆，回傳 JSON 陣列
    """
    if db is None:
        return "[工具錯誤] read_custom_table 需要資料庫連線"

    from app.db.models.fn_custom_table import CustomTableRecord

    target_table_id: int = config.get("target_table_id")
    limit: int = int(config.get("limit", 20))
    scope: str = config.get("scope", "self")
    user_id: int = config.get("user_id")

    if not target_table_id:
        return "[工具錯誤] read_custom_table 設定不完整（缺少 target_table_id）"

    query = db.query(CustomTableRecord).filter(
        CustomTableRecord.table_id == target_table_id
    )

    if scope == "self":
        if not user_id:
            return "[工具錯誤] read_custom_table scope=self 需要 user_id"
        query = query.filter(CustomTableRecord.updated_by == user_id)

    records = query.order_by(CustomTableRecord.updated_at.desc()).limit(limit).all()

    result = [r.data for r in records]
    return json.dumps(result, ensure_ascii=False, default=str)


def _execute_web_scraper(config: dict, tool_input: dict) -> str:  # noqa: ARG001
    """執行 web_scraper 類型工具呼叫。

    流程：
    1. httpx GET target_url（timeout=30s）
    2. BeautifulSoup 清除 script/style/img 取純文字
    3. 截斷至 max_chars 字元
    4. LLM 依 extract_description 解讀並回傳擷取結果
    """
    target_url: str = config.get("target_url", "")
    extract_description: str = config.get("extract_description", "")
    max_chars: int = int(config.get("max_chars", 4000))

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(target_url)
        html_content = resp.text
    except httpx.ConnectError:
        return "無法連線至目標網址"
    except httpx.TimeoutException:
        return "目標網址請求逾時"
    except Exception as exc:
        return f"無法連線至目標網址：{exc}"

    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "img"]):
        tag.decompose()
    plain_text = soup.get_text(separator="\n", strip=True)
    plain_text = plain_text[:max_chars]

    try:
        llm_messages = [
            {
                "role": "user",
                "content": (
                    f"以下是從網頁擷取的純文字內容：\n\n{plain_text}\n\n"
                    f"請依據以下描述，從上述內容中擷取所需資訊並回傳結果：\n{extract_description}"
                ),
            }
        ]
        result = chat(
            model=settings.anthropic_model,
            system="你是一個資料擷取助理，請依據使用者的描述從提供的網頁文字中精確擷取所需資訊，並直接回傳擷取結果。",
            messages=llm_messages,
        )
        return result.get("content", "無法解讀擷取結果")
    except Exception as exc:
        return f"[LLM 解讀失敗] {exc}"
