"""
手動執行完整管線（不透過 Celery 排程）

流程：
1. 每 20 分鐘一段，各自呼叫 flash_task 的 _process_batch（SSB → 預彙總 → Haiku → 合併 → 累計）
2. 呼叫 pro_task 的邏輯（Sonnet 彙整 → 合併寫入 DB）

注意：會呼叫 Claude API（Haiku + Sonnet），執行前確認 API 額度。

用法：
  python scripts/run_pipeline.py          # 預設拉 60 分鐘（3 次 Haiku + 1 次 Sonnet）
  python scripts/run_pipeline.py 20       # 只拉 20 分鐘（1 次 Haiku + 1 次 Sonnet）
"""

import sys
import os
import time
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.security_event import LogBatch
from app.services.ssb_client import SSBClient
from app.tasks.flash_task import _process_batch

# run_pro_task 是 Celery task，直接當函數呼叫即可（不需要 worker）
from app.tasks.pro_task import run_pro_task

INTERVAL = settings.FLASH_INTERVAL_MINUTES


def main():
    total_minutes = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    num_intervals = max(total_minutes // INTERVAL, 1)

    print(f"管線設定: 拉取最近 {total_minutes} 分鐘, 每 {INTERVAL} 分鐘一段")
    print(f"共 {num_intervals} 次 Haiku + 1 次 Sonnet")
    estimated_cost = num_intervals * 0.035 + 0.11
    print(f"預估費用: ~${estimated_cost:.2f} USD")

    db = SessionLocal()
    ssb = SSBClient()

    try:
        now = datetime.now(timezone.utc)

        # ── Flash Task: 每段各跑一次 ──
        for i in range(num_intervals):
            interval_end = now - timedelta(minutes=INTERVAL * (num_intervals - 1 - i))
            interval_start = interval_end - timedelta(minutes=INTERVAL)

            if i > 0:
                print("\n等待 65 秒（rate limit）...")
                time.sleep(65)

            print(f"\n{'=' * 60}")
            print(
                f"區間 {i + 1}/{num_intervals}: {interval_start.strftime('%H:%M')} ~ {interval_end.strftime('%H:%M')}"
            )
            print(f"{'=' * 60}")

            batch = LogBatch(
                time_from=interval_start,
                time_to=interval_end,
                status="running",
            )
            db.add(batch)
            db.commit()

            _process_batch(db, ssb, batch)
            print(f"Batch 狀態: {batch.status}, 拉到 {batch.records_fetched} 筆")

        # ── Pro Task: Sonnet 彙整 + 合併寫入 DB ──
        print(f"\n{'=' * 60}")
        print("Pro Task: Sonnet 彙整")
        print(f"{'=' * 60}")
        print("等待 65 秒（rate limit）...")
        time.sleep(65)

        # pro_task 會自己讀當天累計、呼叫 Sonnet、合併寫入 DB
        run_pro_task()

        print("\n完成！")

    finally:
        db.close()
        ssb.close()


if __name__ == "__main__":
    main()
