import logging
from datetime import date, datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.security_event import (
    DailyAnalysis,
    FlashResult,
    LogBatch,
    SecurityEvent,
)
from app.services.claude_pro import aggregate_daily
from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.pro_task.run_pro_task")
def run_pro_task() -> None:
    """每日凌晨執行。讀取當天累計的 1 筆合併 JSON，送 Sonnet 做最終彙整。"""
    db = SessionLocal()
    today = date.today()
    yesterday = today - timedelta(days=1)

    analysis = DailyAnalysis(
        analysis_date=today,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(analysis)
    db.commit()

    try:
        # 1. 找當天的累計記錄（chunk_index=-1）
        today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        today_batches = (
            db.query(LogBatch.id).filter(LogBatch.time_from >= today_start).subquery()
        )

        accumulator = (
            db.query(FlashResult)
            .filter(
                FlashResult.batch_id.in_(today_batches),
                FlashResult.chunk_index == -1,
                FlashResult.status == "success",
            )
            .first()
        )

        if not accumulator or not accumulator.events:
            logger.info(f"{today}: no accumulated events, skipping Pro Task")
            analysis.status = "success"
            analysis.flash_results_count = 0
            analysis.completed_at = datetime.now(timezone.utc)
            db.commit()
            return

        # 已經是去重合併過的事件，直接以 match_key 為 key 建立 dict
        grouped = {}
        for event in accumulator.events:
            key = event.get("match_key", "unknown")
            grouped[key] = [event]  # 每個 key 只有 1 筆（已合併）

        analysis.flash_results_count = len(grouped)
        db.commit()

        # 2. 取昨天事件（延續判斷用）
        prev_events = (
            db.query(SecurityEvent).filter(SecurityEvent.event_date == yesterday).all()
        )
        prev_summary = [
            {"match_key": e.match_key, "title": e.title, "id": e.id}
            for e in prev_events
        ]

        # 3. 建立 match_key → logs 的 lookup（Sonnet 不回傳 logs，從 accumulator 帶）
        # 同時收集所有 logs 作為 fallback（Sonnet 可能改 match_key）
        logs_by_key = {}
        all_available_logs = []
        for event in accumulator.events:
            key = event.get("match_key", "unknown")
            if event.get("logs"):
                logs_by_key[key] = event["logs"]
                all_available_logs.extend(event["logs"])

        # 4. 送 Claude Sonnet — 資料量已大幅精簡
        final_events = aggregate_daily(grouped, prev_summary, str(today))

        # 5. 寫入 security_events（合併延續事件：同 match_key 且未結案 → UPDATE）
        created = updated = 0
        for ev in final_events:
            ev_logs = (
                ev.get("logs")
                or logs_by_key.get(ev["match_key"])
                or all_available_logs[:5]
            )

            # 先找同 match_key 且未結案的事件（不限日期，合併延續事件）
            existing = (
                db.query(SecurityEvent)
                .filter(
                    SecurityEvent.match_key == ev["match_key"],
                    SecurityEvent.current_status.in_(["pending", "investigating"]),
                )
                .order_by(SecurityEvent.event_date.desc())
                .first()
            )

            if existing:
                # 合併：更新內容，date_end 延伸到今天，detection_count 累加
                for field in [
                    "star_rank",
                    "title",
                    "description",
                    "affected_summary",
                    "affected_detail",
                    "ioc_list",
                    "mitre_tags",
                    "suggests",
                ]:
                    val = ev.get(field)
                    if field == "affected_summary" and val:
                        val = val[:100]
                    if val is not None:
                        setattr(existing, field, val)
                existing.date_end = today
                existing.detection_count = (existing.detection_count or 0) + ev.get(
                    "detection_count", 0
                )
                if ev_logs:
                    existing.logs = ev_logs
                existing.updated_at = datetime.now(timezone.utc)
                updated += 1
            else:
                db.add(
                    SecurityEvent(
                        event_date=today,
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
                created += 1

        db.commit()

        analysis.status = "success"
        analysis.events_created = created
        analysis.events_updated = updated
        analysis.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Pro Task done: {created} created, {updated} updated")

    except Exception as exc:
        analysis.status = "failed"
        analysis.error_message = str(exc)
        db.commit()
        logger.exception(f"Pro Task failed: {exc}")
    finally:
        db.close()
