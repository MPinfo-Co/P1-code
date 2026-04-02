import json
import logging

from anthropic import Anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


SYSTEM_PROMPT = """你是資深資安分析師。根據一整天的 AI 分析結果，產出整合去重後的最終事件清單。

## 事件合併規則（重要）

不同 match_key 的事件，若同時滿足以下三個條件，**必須合併為一筆**：
1. **同一類安全現象**：行為相同（例如都是廣播被擋、都是端口掃描、都是同類型登入失敗）
2. **同一個根因**：多個 IP/主機做同樣的事，來自同一個設定問題或同一波攻擊
3. **同一個處置方式**：資安專家的處理動作相同（例如都是「檢查 NetBIOS 設定」）

常見合併情境：
- 多個內部 IP 發送 NetBIOS 廣播（port 137/138）被擋 → 合併為一筆「內部 NetBIOS 廣播異常」
- 多個 IPv6 link-local 地址的 mDNS/LLMNR/DHCPv6 被擋 → 合併為一筆「IPv6 多播異常」
- 同一來源 IP 對不同目標的掃描 → 合併為一筆

不該合併的情境：
- Administrator 暴力破解 vs 普通帳號密碼錯誤 → 根因不同，分開
- 外部掃描 vs 內部廣播 → 現象不同，分開

安全閥：合併後單一事件不得包含超過 5 個不同的原始 match_key，超過代表太寬泛，應拆分。

## 輸出規則

1. 只輸出 JSON 陣列，不加任何說明文字
2. **match_key 必須原樣使用輸入的某一個 key，禁止修改、重新命名或翻譯**。合併多個事件時，選其中一個原始 match_key
3. 合併時 detection_count 為所有被合併事件的 log 總數加總
4. 合併時 affected_detail 要涵蓋所有被合併事件的受影響 IP/主機
5. 若事件與昨天的事件相同（延續），填入 continued_from_match_key
6. suggests 提供 3-5 條具體處置建議
7. affected_detail 使用【】標籤格式：
   - 【異常發現】必填。用一段話說明發生什麼事，包含受影響的設備/帳號/IP
   - 【風險分析】必填。說明嚴重性、可能後果、為什麼需要關注
   - 【攻擊來源】選填。有明確來源 IP 或主機時才填"""

USER_PROMPT_TEMPLATE = """今天日期：{today}

今天偵測到的事件候選（依 match_key 分群，每群代表同類事件的所有偵測）：
{grouped_events_json}

昨天的已確認事件（用於判斷是否為延續事件）：
{previous_events_json}

請輸出整合後的最終事件清單，每筆格式：
{{
  "match_key": "必須原樣使用輸入的 key，禁止修改",
  "star_rank": 1-5,
  "title": "最終事件標題（50字以內）",
  "description": "事件說明（200字以內）",
  "affected_summary": "20字以內，格式：對象（補充）",
  "affected_detail": "【異常發現】發生什麼事+受影響對象（必填）\\n【風險分析】嚴重性與可能後果（必填）\\n【攻擊來源】IP清單（有明確來源才填）",
  "detection_count": 123,
  "ioc_list": ["IP 或域名"],
  "mitre_tags": ["TXXXX"],
  "suggests": ["處置步驟 1", "處置步驟 2"],
  "continued_from_match_key": "昨天的 match_key（若為延續事件），否則 null"
}}"""


def aggregate_daily(
    grouped_events: dict[str, list[dict]],
    previous_events: list[dict],
    today: str,
) -> list[dict]:
    prompt = USER_PROMPT_TEMPLATE.format(
        today=today,
        grouped_events_json=json.dumps(grouped_events, ensure_ascii=False, indent=2),
        previous_events_json=json.dumps(previous_events, ensure_ascii=False),
    )

    client = _get_client()
    import re
    import time as _time

    for attempt in range(3):
        if attempt > 0:
            logger.warning(f"Sonnet retry {attempt + 1}/3...")
            _time.sleep(65)

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16384,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        text = message.content[0].text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]).strip()

        # 修復常見 JSON 問題：trailing commas
        text = re.sub(r",\s*([}\]])", r"\1", text)

        try:
            events = json.loads(text)
        except json.JSONDecodeError:
            # 嘗試找到 JSON 陣列的範圍
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1:
                text = text[start : end + 1]
                text = re.sub(r",\s*([}\]])", r"\1", text)
                try:
                    events = json.loads(text)
                except json.JSONDecodeError:
                    logger.warning(
                        f"Sonnet attempt {attempt + 1} returned invalid JSON"
                    )
                    continue
            else:
                logger.warning(f"Sonnet attempt {attempt + 1} returned invalid JSON")
                continue

        if not isinstance(events, list):
            logger.warning(f"Sonnet attempt {attempt + 1} returned non-array")
            continue

        return events

    raise ValueError("Sonnet failed to produce valid JSON after 3 attempts")
