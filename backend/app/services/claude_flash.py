import json
import logging
import re

from anthropic import Anthropic

from core.config import settings

logger = logging.getLogger(__name__)

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


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

# ── Dynamic column key prefixes ──
_FORTI_PREFIX = ".sdata.forti."
_WIN_PREFIX = ".sdata.win@18372.4."

# FortiGate 要從 dynamic_columns 提取的欄位
_FORTI_FIELDS = (
    "action",
    "level",
    "subtype",
    "srcip",
    "dstip",
    "dstport",
    "srccountry",
    "service",
)

# Windows 要從 dynamic_columns 提取的欄位
_WIN_FIELDS = (
    "event_id",
    "event_username",
    "event_host",
    "event_type",
    "event_category",
)

# Windows message 尾巴固定說明文字的截斷 pattern
_WIN_MSG_TAIL_PATTERNS = [
    re.compile(r"\r?\n\r?\n當.*$", re.DOTALL),  # 中文：「當...就會產生這個事件」
    re.compile(r"\s*此事件會在.*$", re.DOTALL),  # 中文變體
    re.compile(r"\s*這個事件會在.*$", re.DOTALL),  # 中文變體
    re.compile(
        r"\r?\n\r?\nThis event is (?:generated|logged) when.*$",
        re.DOTALL | re.IGNORECASE,
    ),  # 英文
]

# 舊版保留欄位（fallback 用）
_KEEP_FIELDS = ("id", "timestamp", "host", "program", "message")


def _trim_windows_message(message: str) -> str:
    """移除 Windows log message 尾巴的固定說明文字，節省 token。"""
    if not message:
        return message
    for pattern in _WIN_MSG_TAIL_PATTERNS:
        message = pattern.sub("", message)
    return message.strip()


def _slim_log(log: dict) -> dict:
    """
    根據 log 類型做不同精簡：
    - FortiGate：不送 message，從 dynamic_columns 取結構化欄位
    - Windows：從 dynamic_columns 取結構化欄位 + 精簡 message
    - 其他：保留基本欄位（fallback）
    """
    dc = log.get("dynamic_columns", {})

    # FortiGate log
    if any(k.startswith(_FORTI_PREFIX) for k in dc):
        slim = {
            "id": log.get("id", ""),
            "timestamp": log.get("timestamp", ""),
            "host": log.get("host", ""),
        }
        for field in _FORTI_FIELDS:
            val = dc.get(f"{_FORTI_PREFIX}{field}")
            if val:
                slim[field] = val
        return slim

    # Windows log
    if any(k.startswith(_WIN_PREFIX) for k in dc):
        slim = {
            "id": log.get("id", ""),
            "timestamp": log.get("timestamp", ""),
            "host": log.get("host", ""),
        }
        for field in _WIN_FIELDS:
            val = dc.get(f"{_WIN_PREFIX}{field}")
            if val:
                slim[field] = val
        # 保留 message 但精簡
        message = log.get("message", "")
        if message:
            slim["message"] = _trim_windows_message(message)
        return slim

    # Fallback：舊行為
    return {k: log[k] for k in _KEEP_FIELDS if k in log}


def analyze_chunk(logs: list[dict]) -> list[dict]:
    """
    送一批 log 給 Claude Haiku 分析。

    logs 可以是混合格式：原始 log（會被 _slim_log 精簡）和
    FortiGate 彙總摘要（type 為 deny_external/deny_internal/warning，直接使用）。
    """
    processed = []
    for log in logs:
        # FortiGate 彙總摘要已經是精簡格式，直接使用
        if log.get("type") in ("deny_external", "deny_internal", "warning"):
            processed.append(log)
        else:
            processed.append(_slim_log(log))

    prompt = USER_PROMPT_TEMPLATE.format(
        chunk_size=len(processed),
        logs_json=json.dumps(processed, ensure_ascii=False),
    )

    client = _get_client()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]).strip()

    events = json.loads(text)
    if not isinstance(events, list):
        raise ValueError(f"Claude returned non-array: {type(events)}")

    return events


def analyze_chunk_with_usage(logs: list[dict]) -> tuple[list[dict], dict]:
    """
    同 analyze_chunk，但額外回傳 token usage 資訊。
    Returns: (events, usage_dict)
    """
    processed = []
    for log in logs:
        if log.get("type") in ("deny_external", "deny_internal", "warning"):
            processed.append(log)
        else:
            processed.append(_slim_log(log))

    prompt = USER_PROMPT_TEMPLATE.format(
        chunk_size=len(processed),
        logs_json=json.dumps(processed, ensure_ascii=False),
    )

    client = _get_client()
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    usage = {
        "input_tokens": message.usage.input_tokens,
        "output_tokens": message.usage.output_tokens,
    }

    text = message.content[0].text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]).strip()

    events = json.loads(text)
    if not isinstance(events, list):
        raise ValueError(f"Claude returned non-array: {type(events)}")

    return events, usage
