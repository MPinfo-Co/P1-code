"""
方案 B 完整管線測試 + 與舊方法比較

流程：
1. 從 SSB 拉取最近 10 分鐘 log（同時用 full search expression）
2. 方案 B：preaggregate → Haiku（記錄 token usage）→ merge
3. Sonnet 彙整
4. 印出比較報告（不寫 DB，避免污染現有資料）

注意：會呼叫 Claude API（Haiku + Sonnet），執行前確認 API 額度。
"""

import json
import sys
import time
from datetime import datetime, timedelta


# 加入 backend 路徑
sys.path.insert(0, "/mnt/c/Users/MP0451.MPINFO/Desktop/code test/backend")

from app.core.config import settings
from app.services.claude_flash import analyze_chunk_with_usage
from app.services.log_preaggregator import preaggregate
from app.tasks.flash_task import (
    _merge_events,
    _attach_raw_logs,
    _build_key_lookup,
    _build_summary_key_lookup,
    _override_match_keys,
)


def pull_ssb_logs(minutes: int = 10) -> list[dict]:
    """從 SSB 拉取最近 N 分鐘的 log（使用 SSBClient 含分頁）。"""
    from app.services.ssb_client import SSBClient

    ssb = SSBClient()
    now = datetime.now()
    time_from = now - timedelta(minutes=minutes)
    search_expr = settings.SSB_SEARCH_EXPRESSION
    print(f"  時間範圍: {time_from} ~ {now}")
    print(f"  search_expression: {search_expr[:80]}...")

    try:
        logs = ssb.fetch_logs(time_from, now, search_expr)
    finally:
        ssb.close()
    return logs


def run_plan_b(logs: list[dict]) -> dict:
    """跑方案 B 管線，回傳完整結果。"""
    result = {
        "raw_log_count": len(logs),
        "chunks": [],
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "haiku_cost": 0.0,
        "events_before_merge": [],
        "events_after_merge": [],
    }

    # 1. 分類統計
    forti_count = 0
    win_count = 0
    for log in logs:
        dc = log.get("dynamic_columns", {})
        if any(k.startswith(".sdata.forti.") for k in dc):
            forti_count += 1
        elif any(k.startswith(".sdata.win@18372.4.") for k in dc):
            win_count += 1
    result["forti_raw_count"] = forti_count
    result["windows_raw_count"] = win_count

    # 2. 預彙總
    forti_summaries, windows_logs = preaggregate(logs)
    ai_input = forti_summaries + windows_logs
    result["forti_summary_count"] = len(forti_summaries)
    result["windows_pass_through"] = len(windows_logs)
    result["ai_input_count"] = len(ai_input)

    print(f"\n{'=' * 60}")
    print(f"原始 log: {len(logs)} 筆")
    print(f"  FortiGate: {forti_count} 筆 → 預彙總為 {len(forti_summaries)} 筆摘要")
    print(f"  Windows:   {win_count} 筆 → 原樣通過")
    print(
        f"  送 AI:     {len(ai_input)} 筆（省 {100 * (1 - len(ai_input) / max(len(logs), 1)):.1f}%）"
    )
    print(f"{'=' * 60}\n")

    # 3. 切 chunk + Haiku 分析
    chunk_size = settings.FLASH_CHUNK_SIZE
    all_events = []

    # 方案 B 送 AI 的量很小，通常 1 chunk 就夠
    for idx in range(0, max(len(ai_input), 1), chunk_size):
        chunk = ai_input[idx : idx + chunk_size]
        chunk_num = idx // chunk_size

        if chunk_num > 0:
            print("等待 65 秒（rate limit）...")
            time.sleep(65)

        print(f"Chunk {chunk_num}: {len(chunk)} 筆 → Haiku...")
        events, usage = analyze_chunk_with_usage(chunk)

        # 用原始 logs + 摘要的 group_key 建 key lookup
        key_lookup = _build_key_lookup(logs)
        summary_key_lookup = _build_summary_key_lookup(ai_input)
        _override_match_keys(events, key_lookup, summary_key_lookup)
        _attach_raw_logs(events, logs)

        result["chunks"].append(
            {
                "chunk_index": chunk_num,
                "chunk_size": len(chunk),
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "event_count": len(events),
            }
        )
        result["total_input_tokens"] += usage["input_tokens"]
        result["total_output_tokens"] += usage["output_tokens"]

        print(
            f"  → {len(events)} 事件, "
            f"input: {usage['input_tokens']:,} tokens, "
            f"output: {usage['output_tokens']:,} tokens"
        )

        all_events.extend(events)

    # Haiku 成本：input $0.80/M, output $4.00/M
    result["haiku_cost"] = (
        result["total_input_tokens"] * 0.80 / 1_000_000
        + result["total_output_tokens"] * 4.00 / 1_000_000
    )
    result["events_before_merge"] = all_events

    # 4. 合併
    merged = _merge_events(all_events)
    result["events_after_merge"] = merged

    print(f"\n合併: {len(all_events)} → {len(merged)} 事件")
    print(f"Haiku 總成本: ${result['haiku_cost']:.4f}")
    print(f"  input: {result['total_input_tokens']:,} tokens")
    print(f"  output: {result['total_output_tokens']:,} tokens")

    return result


def print_comparison(plan_b: dict):
    """印出與舊方法的比較報告。"""
    # 舊方法基準（batch 5: 1412 logs, 5 chunks）
    old = {
        "raw_log_count": 1412,
        "chunks": 5,
        "est_input_tokens": 101_000 * 5,  # ~101K per chunk × 5
        "est_haiku_cost": 0.11 * 5,  # ~$0.11 per chunk × 5
        "events_from_haiku": 7,
        "events_after_sonnet": 5,
        "event_titles": [
            "大量外部多源掃描攻擊 - 目標 211.21.43.0/24 (star:4)",
            "多國來源IP大量掃描防火牆公開端口 (star:3)",
            "內部主機大量 NetBIOS 廣播異常 (star:3)",
            "FortiClient VPN 出現身份不明連線 (star:2)",
            "IPv6 mDNS 多播流量遭防火牆攔截 (star:2)",
        ],
    }

    print(f"\n{'=' * 60}")
    print("  方案 B vs 舊方法 比較報告")
    print(f"{'=' * 60}\n")

    print(f"{'指標':<30} {'舊方法':>15} {'方案B':>15} {'節省':>10}")
    print(f"{'-' * 70}")
    print(
        f"{'原始 log 數':<30} {old['raw_log_count']:>15} {plan_b['raw_log_count']:>15}"
    )
    print(
        f"{'送 AI 筆數':<30} {old['raw_log_count']:>15} {plan_b['ai_input_count']:>15} {100 * (1 - plan_b['ai_input_count'] / max(old['raw_log_count'], 1)):>9.1f}%"
    )
    print(f"{'Chunk 數':<30} {old['chunks']:>15} {len(plan_b['chunks']):>15}")
    print(
        f"{'Input tokens（估）':<30} {old['est_input_tokens']:>15,} {plan_b['total_input_tokens']:>15,} {100 * (1 - plan_b['total_input_tokens'] / max(old['est_input_tokens'], 1)):>9.1f}%"
    )
    old_cost_str = f"${old['est_haiku_cost']:.4f}"
    new_cost_str = f"${plan_b['haiku_cost']:.4f}"
    cost_saving = 100 * (1 - plan_b["haiku_cost"] / max(old["est_haiku_cost"], 1))
    print(
        f"{'Haiku 費用':<30} {old_cost_str:>15} {new_cost_str:>15} {cost_saving:>9.1f}%"
    )
    print(
        f"{'Haiku 事件數':<30} {old['events_from_haiku']:>15} {len(plan_b['events_before_merge']):>15}"
    )
    print(
        f"{'合併後事件數':<30} {old['events_after_sonnet']:>15} {len(plan_b['events_after_merge']):>15}"
    )

    # 每日成本推估（144 次/天）
    old_daily = old["est_haiku_cost"] * 144
    new_daily = plan_b["haiku_cost"] * 144
    print(
        f"\n{'每日 Haiku 成本推估':<30} {'$' + f'{old_daily:.2f}':>15} {'$' + f'{new_daily:.2f}':>15} {100 * (1 - new_daily / max(old_daily, 1)):>9.1f}%"
    )
    print(
        f"{'每月 Haiku 成本推估':<30} {'$' + f'{old_daily * 30:.0f}':>15} {'$' + f'{new_daily * 30:.0f}':>15}"
    )

    print("\n--- 方案 B 事件詳情 ---")
    for ev in plan_b["events_after_merge"]:
        print(f"\n  [{ev.get('star_rank', '?')}星] {ev.get('title', 'N/A')}")
        print(f"  match_key: {ev.get('match_key', 'N/A')}")
        print(f"  detection_count: {ev.get('detection_count', 0)}")
        detail = ev.get("affected_detail", "")
        if detail:
            # 只印前 150 字
            print(f"  detail: {detail[:150]}...")

    print("\n--- 舊方法事件（基準）---")
    for title in old["event_titles"]:
        print(f"  {title}")


def main():
    print("=" * 60)
    print("方案 B 完整管線測試")
    print(f"時間: {datetime.now()}")
    print("=" * 60)

    # 1. 拉 log
    print("\n[1] 從 SSB 拉取最近 10 分鐘 log...")
    logs = pull_ssb_logs(minutes=10)
    print(f"拉到 {len(logs)} 筆 log")

    if not logs:
        print("沒有 log，結束")
        return

    # 2. 跑方案 B
    print("\n[2] 跑方案 B 管線...")
    plan_b = run_plan_b(logs)

    # 3. 比較報告
    print("\n[3] 產出比較報告...")
    print_comparison(plan_b)

    # 4. 存結果 JSON（給後續分析用）
    output = {
        "timestamp": datetime.now().isoformat(),
        "raw_log_count": plan_b["raw_log_count"],
        "forti_raw_count": plan_b["forti_raw_count"],
        "windows_raw_count": plan_b["windows_raw_count"],
        "forti_summary_count": plan_b["forti_summary_count"],
        "ai_input_count": plan_b["ai_input_count"],
        "chunks": plan_b["chunks"],
        "total_input_tokens": plan_b["total_input_tokens"],
        "total_output_tokens": plan_b["total_output_tokens"],
        "haiku_cost": plan_b["haiku_cost"],
        "events_before_merge_count": len(plan_b["events_before_merge"]),
        "events_after_merge_count": len(plan_b["events_after_merge"]),
        "events": [
            {
                "star_rank": ev.get("star_rank"),
                "title": ev.get("title"),
                "match_key": ev.get("match_key"),
                "detection_count": ev.get("detection_count"),
                "affected_summary": ev.get("affected_summary"),
                "affected_detail": ev.get("affected_detail"),
                "log_count": len(ev.get("logs", [])),
            }
            for ev in plan_b["events_after_merge"]
        ],
    }
    out_path = (
        "/mnt/c/Users/MP0451.MPINFO/Desktop/code test/backend/scripts/planb_result.json"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n結果已存到: {out_path}")


if __name__ == "__main__":
    main()
