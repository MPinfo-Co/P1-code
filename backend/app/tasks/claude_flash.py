# app/tasks/claude_flash.py
"""Haiku per-chunk security event extraction.

Public entry: analyze_chunk(logs, *, client=None) -> list[dict]
"""

from __future__ import annotations
import json
from anthropic import Anthropic
from app.config.settings import settings

MODEL = "claude-haiku-4-5-20251001"
MAX_TOKENS = 4096

# Lifted verbatim from app/tasks/old_task/claude_flash.py:21-40 (load-bearing
# domain prompt — defines event taxonomy, star_rank, affected_detail format).
SYSTEM_PROMPT = """你是資安事件分析師。分析輸入的 syslog 資料，找出所有值得關注的資安事件。
規則：
1. 只輸出 JSON 陣列，不加任何說明文字、markdown 或程式碼區塊
2. 若無資安事件，輸出空陣列 []
3. star_rank 定義：1=正常資訊 2=低風險 3=中風險 4=高風險 5=緊急
4. affected_summary：20 字以內，格式「{主要對象}（{最關鍵補充}）」
5. affected_detail 使用【】標籤格式，規範如下：
   - 【異常發現】必填。用一段話說明發生什麼事，包含受影響的設備/帳號/IP
   - 【風險分析】必填。說明這件事的嚴重性、可能後果、為什麼需要關注
   - 【攻擊來源】選填。有明確來源 IP 或主機時才填，列出 IP 清單
6. match_key 規則：
   - 如果資料中有 group_key 欄位，必須直接使用 group_key 的值作為 match_key（不可修改）
   - 只有沒有 group_key 的資料才需要自行產生 match_key（全英文/數字/底線）
7. log_ids 規則：
   - Windows log：使用 log 的 id 值
   - FortiGate 彙總摘要：使用 representative_log_ids 欄位中的值
8. 輸入資料有兩種格式：
   - Windows log：包含 event_id、event_username 等結構化欄位 + 精簡後的 message
   - FortiGate 彙總摘要：type 為 deny_external/deny_internal/warning，包含統計資訊（total_count、IP 清單等），這些是預彙總後的資料，代表該時段的統計。每筆摘要帶有 group_key（用於事件合併）和 representative_log_ids（用於溯源）
   兩種格式都要分析，FortiGate 摘要代表該時段的彙總統計。"""

# Lifted verbatim from app/tasks/old_task/claude_flash.py:42-57.
USER_PROMPT_TEMPLATE = """以下是 {chunk_size} 筆資安相關資料（含 Windows log 和/或 FortiGate 彙總摘要），請分析並輸出資安事件 JSON 陣列。

每筆事件格式：
{{
  "star_rank": 1-5,
  "title": "事件標題（50字以內）",
  "affected_summary": "20字以內，格式：對象（補充）",
  "affected_detail": "【異常發現】發生什麼事+受影響對象（必填）\\n【風險分析】嚴重性與可能後果（必填）\\n【攻擊來源】IP清單（有明確來源才填）",
  "match_key": "英文_底線_格式",
  "log_ids": ["log 的 id 值（字串）"],
  "ioc_list": ["IP 或域名"],
  "mitre_tags": ["TXXXX"]
}}

資料：
{logs_json}"""


def analyze_chunk(logs: list[dict], *, client: Anthropic | None = None) -> list[dict]:
    """Analyze a batch of logs with Claude Haiku and return security events.

    Args:
        logs: Mixed list of pre-aggregated FortiGate summaries and Windows logs.
        client: Optional Anthropic client; a new one is created if not provided.

    Returns:
        List of security event dicts as returned by the model.
    """
    if not logs:
        return []
    ant = client or Anthropic(api_key=settings.anthropic_api_key)
    prompt = USER_PROMPT_TEMPLATE.format(
        chunk_size=len(logs),
        logs_json=json.dumps(logs, ensure_ascii=False),
    )
    msg = ant.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(msg.content[0].text)
