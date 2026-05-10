"""LLM Client — 封裝單次 Anthropic API 呼叫。

職責：
- 提供 chat() 介面，執行單次 LLM 呼叫
- 自動 retry（最多 3 次，指數退避：1s → 2s → 4s）
- 超過 retry 次數或非 5xx 錯誤 → raise LLMClientError

不處理 tool_call 迴圈（由 ai_agent.py 負責）。
"""

import time

import anthropic

from app.config.settings import settings


class LLMClientError(Exception):
    """LLM 呼叫失敗，上層捕捉後統一回傳 503。"""


# Singleton Anthropic client；模組載入時建立一次，所有呼叫共用。
_client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=60.0)


def chat(
    model: str,
    system: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> dict:
    """執行單次 Anthropic LLM 呼叫，含 retry 邏輯。

    Args:
        model: 模型名稱（如 claude-sonnet-4-6）。
        system: System prompt 字串。
        messages: 對話歷史，格式：[{"role": "user/assistant", "content": "..."}]。
        tools: Anthropic tool_use 格式的工具定義陣列；無工具時傳 None。
        max_tokens: 最大回覆 token 數，預設 4096。
        temperature: 回覆隨機程度，預設 0.7。

    Returns:
        dict: {
            "content": str,           # AI 回覆文字內容
            "tool_calls": list[dict]  # tool_use 結果；無時為空陣列
        }

    Raises:
        LLMClientError: API 呼叫失敗且 retry 耗盡，或非 retryable 錯誤。
    """
    kwargs: dict = {
        "model": model,
        "system": system,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools

    max_retries = 3
    delay = 1.0

    for attempt in range(max_retries + 1):
        try:
            response = _client.messages.create(**kwargs)
            break
        except anthropic.BadRequestError as exc:
            # 400 — 不 retry；先辨別常見原因
            msg = str(exc).lower()
            if "credit balance is too low" in msg:
                raise LLMClientError("AI 服務餘額不足，請聯絡管理員補充點數")
            raise LLMClientError("LLM 呼叫失敗：請求參數錯誤（token 超限或格式問題）")
        except anthropic.AuthenticationError:
            raise LLMClientError("LLM 呼叫失敗：API Key 驗證失敗")
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as exc:
            if attempt >= max_retries:
                raise LLMClientError(f"LLM 呼叫失敗，retry 耗盡：{exc}") from exc
            time.sleep(delay)
            delay *= 2
        except anthropic.APIError as exc:
            if attempt >= max_retries:
                raise LLMClientError(f"LLM 呼叫失敗：{exc}") from exc
            time.sleep(delay)
            delay *= 2

    # 解析回應
    content_text = ""
    tool_calls: list[dict] = []

    for block in response.content:
        if block.type == "text":
            content_text = block.text
        elif block.type == "tool_use":
            tool_calls.append(
                {
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                }
            )

    return {"content": content_text, "tool_calls": tool_calls}
