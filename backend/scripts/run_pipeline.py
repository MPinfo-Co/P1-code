"""
手動執行一次完整管線（不透過 Celery 排程）

流程：
1. 登入 SSB，拉取最近 10 分鐘的 log
2. 預彙總 FortiGate log（full 模式）
3. 切成 chunk，逐一送 Haiku 分析
4. 程式產 group_key 覆蓋 AI 的 match_key，attach 原始 log
5. 合併同 group_key 事件
6. 送 Sonnet 做最終彙整
7. 寫入 security_events DB

注意：會呼叫 Claude API（Haiku + Sonnet），執行前確認 API 額度。
"""

import sys
import time
from datetime import datetime, timezone, timedelta, date

sys.path.insert(0, "/mnt/c/Users/MP0451.MPINFO/Desktop/code test/backend")

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.security_event import LogBatch, FlashResult, SecurityEvent
from app.services.claude_flash import analyze_chunk
from app.services.claude_pro import aggregate_daily
from app.services.log_preaggregator import preaggregate
from app.services.ssb_client import SSBClient
from app.tasks.flash_task import (
    _merge_events,
    _attach_raw_logs,
    _build_key_lookup,
    _build_summary_key_lookup,
    _override_match_keys,
)


def main():
    db = SessionLocal()
    ssb = SSBClient()

    try:
        # ── 1. 拉 SSB log ──
        now = datetime.now()
        time_from = now - timedelta(minutes=10)
        search_expr = settings.effective_search_expression

        print(f"拉取 SSB log: {time_from} ~ {now}")
        logs = ssb.fetch_logs(time_from, now, search_expr)
        print(f"拉到 {len(logs)} 筆")

        if not logs:
            print("沒有 log，結束")
            return

        # ── 2. 預彙總（full 模式）──
        summary_key_lookup = None
        if settings.ANALYSIS_MODE == "full":
            forti_summaries, windows_logs = preaggregate(logs)
            ai_input = forti_summaries + windows_logs
            summary_key_lookup = _build_summary_key_lookup(ai_input)
            print(
                f"預彙總: {len(logs)} 筆 -> "
                f"{len(forti_summaries)} FortiGate 摘要 + "
                f"{len(windows_logs)} Windows log = {len(ai_input)} 筆送 AI"
            )
        else:
            ai_input = logs

        # ── 3. 建 batch ──
        batch = LogBatch(
            time_from=time_from,
            time_to=now,
            status="running",
            records_fetched=len(logs),
        )
        db.add(batch)
        db.commit()

        # ── 4. 切 chunk + Haiku 分析 ──
        chunk_size = settings.FLASH_CHUNK_SIZE
        all_events = []
        for idx in range(0, max(len(ai_input), 1), chunk_size):
            chunk = ai_input[idx : idx + chunk_size]
            chunk_num = idx // chunk_size
            if chunk_num > 0:
                time.sleep(65)  # rate limit: 50K tokens/min
            print(f"Chunk {chunk_num}: {len(chunk)} 筆 -> Haiku...")

            fr = FlashResult(
                batch_id=batch.id,
                chunk_index=chunk_num,
                chunk_size=len(chunk),
                status="pending",
            )
            db.add(fr)
            db.commit()

            events = analyze_chunk(chunk)
            key_lookup = _build_key_lookup(logs)
            _override_match_keys(events, key_lookup, summary_key_lookup)
            _attach_raw_logs(events, logs)

            fr.events = events
            fr.status = "success"
            fr.processed_at = datetime.now(timezone.utc)
            db.commit()

            all_events.extend(events)
            print(f"  -> {len(events)} 事件")

        # ── 5. 合併 ──
        merged = _merge_events(all_events)
        print(f"合併: {len(all_events)} -> {len(merged)}")

        # ── 6. Sonnet 彙整 ──
        print("等待 65 秒（rate limit）...")
        time.sleep(65)
        grouped = {ev["match_key"]: [ev] for ev in merged}
        logs_by_key = {ev["match_key"]: ev.get("logs", []) for ev in merged}
        final = aggregate_daily(grouped, [], str(date.today()))
        print(f"Sonnet -> {len(final)} 事件")

        # ── 7. 寫入 DB ──
        for ev in final:
            # Sonnet 可能改 match_key，用 logs fallback 找回原始 key 的 logs
            ev_logs = ev.get("logs") or logs_by_key.get(ev["match_key"]) or []
            if not ev_logs:
                # fallback: 給前 5 筆任意 logs
                all_logs = [log for m in merged for log in m.get("logs", [])]
                ev_logs = all_logs[:5]
            db.add(
                SecurityEvent(
                    event_date=date.today(),
                    star_rank=ev["star_rank"],
                    title=ev["title"],
                    description=ev.get("description"),
                    affected_summary=(ev.get("affected_summary") or "")[:100],
                    affected_detail=ev.get("affected_detail"),
                    match_key=ev["match_key"],
                    detection_count=ev.get("detection_count", 0),
                    logs=ev_logs,
                    ioc_list=ev.get("ioc_list"),
                    mitre_tags=ev.get("mitre_tags"),
                    suggests=ev.get("suggests"),
                )
            )
        db.commit()

        batch.status = "success"
        db.commit()

        print(f"\n完成！共 {len(final)} 筆事件寫入 DB")
        for ev in final:
            print(
                f"  [{ev['star_rank']}星] {ev['title']} (match_key: {ev['match_key']})"
            )

    finally:
        db.close()
        ssb.close()


if __name__ == "__main__":
    main()
