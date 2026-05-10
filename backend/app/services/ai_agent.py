"""AI Agent — 執行 agentic loop。

職責：
- 呼叫 llm_client.chat()
- 判斷 tool_call，執行外部工具 API
- 帶回 tool_result 繼續對話
- 迴圈上限 5 次，超過則 raise AgentMaxIterationError
- URL 樣板替換（{xxx} → tool input 參數值）
"""

import httpx

from app.services.llm_client import LLMClientError, chat  # noqa: F401 (re-export for convenience)


class AgentMaxIterationError(Exception):
    """agentic loop 達到迴圈上限（5 次），上層捕捉後回傳 503。"""


def run(
    model: str,
    system: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    tool_configs: list[dict] | None = None,
) -> dict:
    """執行完整 agentic loop，回傳最終 AI 回覆與 tool_use 結果。

    Args:
        model: 模型名稱。
        system: 組裝完成的 system prompt。
        messages: 對話歷史（含本輪 user message）。
        tools: Anthropic tool_use 格式的工具定義清單；無工具時傳 None。
        tool_configs: 對應 tools 的執行設定（endpoint_url, http_method, auth_type 等）；
                      無工具時傳 None。

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

    while True:
        result = chat(
            model=model,
            system=system,
            messages=current_messages,
            tools=tools,
        )

        tool_calls = result.get("tool_calls", [])

        # 無 tool_call → 對話結束，回傳最終結果
        if not tool_calls:
            return result

        # 有 tool_call → 執行外部工具
        iteration += 1
        if iteration >= MAX_ITERATIONS:
            raise AgentMaxIterationError(
                f"agentic loop 達到迴圈上限（{MAX_ITERATIONS} 次）"
            )

        # 將 assistant 的 tool_use 回應附加到 messages
        # Anthropic 格式：assistant message 的 content 為 block 陣列
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

        # 執行每個 tool_call，收集 tool_result
        tool_results = []
        for tc in tool_calls:
            tool_result_content = _execute_tool(tc, tool_configs or [])
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tc["id"],
                    "content": tool_result_content,
                }
            )

        # 將 tool_result 附加到 messages（user role）
        current_messages.append({"role": "user", "content": tool_results})


def _execute_tool(tool_call: dict, tool_configs: list[dict]) -> str:
    """執行單一工具呼叫，回傳結果字串。

    Args:
        tool_call: {"id": ..., "name": ..., "input": {...}}
        tool_configs: 工具執行設定清單（來自 tb_tools + tb_tool_body_params）

    Returns:
        str: 工具執行結果（或錯誤訊息）
    """
    tool_name = tool_call["name"]
    tool_input = tool_call.get("input", {})

    # 找對應的 tool_config
    config = next((c for c in tool_configs if c.get("name") == tool_name), None)
    if config is None:
        return f"[工具錯誤] 找不到工具設定：{tool_name}"

    # URL 樣板替換
    endpoint_url: str = config.get("endpoint_url", "")
    for key, value in tool_input.items():
        endpoint_url = endpoint_url.replace(f"{{{key}}}", str(value))

    http_method: str = config.get("http_method", "GET").upper()
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
