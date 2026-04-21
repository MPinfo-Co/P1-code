import logging
import time
from collections import defaultdict
from datetime import date, datetime, timezone

from core.config import settings
from models.security_event import FlashResult, LogBatch
from schemas.log_batch import IngestPayload
from services.claude_flash import analyze_chunk

logger = logging.getLogger(__name__)

# ── Dynamic column key prefixes ──
_FORTI_PREFIX = ".sdata.forti."
_WIN_PREFIX = ".sdata.win@18372.4."


def _is_external_ip(ip: str) -> bool:
    """判斷 IP 是否為外部（非 RFC1918 私有位址）。"""
    if not ip:
        return False
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    if parts[0] == "10":
        return False
    if parts[0] == "172" and 16 <= int(parts[1]) <= 31:
        return False
    if parts[0] == "192" and parts[1] == "168":
        return False
    return True


def _is_broadcast_or_multicast(ip: str) -> bool:
    """判斷 IP 是否為廣播或多播地址（適用 IPv4 和 IPv6）。"""
    if not ip:
        return False
    # IPv6 multicast (ff00::/8)
    if ip.lower().startswith("ff"):
        return True
    parts = ip.split(".")
    if len(parts) == 4:
        # IPv4 broadcast (x.x.x.255)
        if parts[3] == "255":
            return True
        # IPv4 multicast (224.0.0.0 ~ 239.255.255.255)
        try:
            if 224 <= int(parts[0]) <= 239:
                return True
        except ValueError:
            pass
    return False


def _generate_group_key(log: dict) -> str | None:
    """
    從 raw log 的 dynamic_columns 產生 group_key（用於合併同類事件）。

    FortiGate deny（外部來源）: deny_external_{dstip前三段}
    FortiGate deny（內部來源）: deny_internal_{srcip}
    FortiGate warning:          warning_{subtype}
    Windows:                    {event_id}_{username}
    """
    dc = log.get("dynamic_columns", {})

    # FortiGate
    action = dc.get(f"{_FORTI_PREFIX}action")
    if action:
        srcip = dc.get(f"{_FORTI_PREFIX}srcip", "")
        dstip = dc.get(f"{_FORTI_PREFIX}dstip", "unknown")
        subtype = dc.get(f"{_FORTI_PREFIX}subtype", "unknown")
        level = dc.get(f"{_FORTI_PREFIX}level", "")

        if action == "deny":
            if _is_external_ip(srcip):
                dst_prefix = ".".join(dstip.split(".")[:3]) if dstip else "unknown"
                return f"deny_external_{dst_prefix}"
            else:
                if _is_broadcast_or_multicast(dstip):
                    dstport = dc.get(f"{_FORTI_PREFIX}dstport", "unknown")
                    return f"deny_internal_broadcast_p{dstport}"
                return f"deny_internal_{srcip}"

        if level == "warning":
            return f"warning_{subtype}"

        return f"forti_{action}_{subtype}"

    # Windows
    event_id = dc.get(f"{_WIN_PREFIX}event_id")
    if event_id:
        username = dc.get(f"{_WIN_PREFIX}event_username", "unknown")
        if "\\" in username:
            username = username.split("\\")[-1]
        username = username.strip().lower().replace(" ", "_") if username else "unknown"
        return f"{event_id}_{username}"

    return None


def _build_key_lookup(chunk: list[dict]) -> dict[str, str]:
    """
    為一個 chunk 裡的每條 log 建立 {ssb_id: group_key} 的 lookup。
    """
    lookup = {}
    for log in chunk:
        ssb_id = str(log.get("id", ""))
        key = _generate_group_key(log)
        if ssb_id and key:
            lookup[ssb_id] = key
    return lookup


def _build_summary_key_lookup(ai_input: list[dict]) -> dict[str, str]:
    """
    從預彙總摘要中建立 {representative_log_id: group_key} 的 lookup。
    只處理有 group_key 和 representative_log_ids 的摘要項目。
    """
    lookup = {}
    for item in ai_input:
        group_key = item.get("group_key")
        rep_ids = item.get("representative_log_ids", [])
        if group_key and rep_ids:
            for rid in rep_ids:
                lookup[str(rid)] = group_key
    return lookup


def _merge_events(all_events: list[dict]) -> list[dict]:
    """
    程式層去重合併：同一個 match_key 的事件合在一起。
    - detection_count / log_ids 加總
    - star_rank 取最高
    - ioc_list / mitre_tags 聯集
    - 其他欄位取第一筆
    """
    grouped = defaultdict(list)
    for ev in all_events:
        grouped[ev.get("match_key", "unknown")].append(ev)

    merged = []
    for match_key, events in grouped.items():
        base = dict(events[0])

        base["star_rank"] = max(ev.get("star_rank", 1) for ev in events)

        all_log_ids = []
        for ev in events:
            all_log_ids.extend(ev.get("log_ids", []))
        base["log_ids"] = list(set(all_log_ids))

        base["detection_count"] = len(base["log_ids"])

        all_ioc = set()
        for ev in events:
            all_ioc.update(ev.get("ioc_list", []))
        base["ioc_list"] = list(all_ioc)

        all_mitre = set()
        for ev in events:
            all_mitre.update(ev.get("mitre_tags", []))
        base["mitre_tags"] = list(all_mitre)

        all_logs = []
        seen_ids = set()
        for ev in events:
            for log in ev.get("logs", []):
                log_id = log.get("id", "")
                if log_id and log_id not in seen_ids:
                    seen_ids.add(log_id)
                    all_logs.append(log)
        base["logs"] = all_logs[:5]

        merged.append(base)

    return merged


def _update_daily_accumulator(db, today: date, batch_merged: list[dict]) -> None:
    """
    把本次 batch 合併後的事件，merge 進當天的累計 flash_result（chunk_index=-1）。
    Sonnet 只需要讀這一筆。
    """
    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    today_batches = (
        db.query(LogBatch.id).filter(LogBatch.time_from >= today_start).subquery()
    )

    accumulator = (
        db.query(FlashResult)
        .filter(
            FlashResult.batch_id.in_(today_batches),
            FlashResult.chunk_index == -1,
        )
        .first()
    )

    if accumulator and accumulator.events:
        all_events = list(accumulator.events) + batch_merged
        accumulator.events = _merge_events(all_events)
        accumulator.processed_at = datetime.now(timezone.utc)
    elif accumulator:
        accumulator.events = batch_merged
        accumulator.processed_at = datetime.now(timezone.utc)
    else:
        any_batch = db.query(LogBatch).filter(LogBatch.time_from >= today_start).first()
        if any_batch:
            acc = FlashResult(
                batch_id=any_batch.id,
                chunk_index=-1,
                chunk_size=0,
                events=batch_merged,
                status="success",
                processed_at=datetime.now(timezone.utc),
            )
            db.add(acc)

    db.commit()
    logger.info(
        f"Daily accumulator updated: {len(accumulator.events if accumulator and accumulator.events else batch_merged)} events total"
    )


def _attach_raw_logs(events: list[dict], chunk: list[dict], max_logs: int = 5) -> None:
    """
    用 Haiku 回傳的 log_ids 從原始 chunk 撈出對應的原始 log。
    log_ids 可能是 SSB 的 id 或 timestamp，兩種都建 lookup。
    最多保留 max_logs 條，確保可溯源回 SSB。
    """
    id_lookup = {}
    ts_lookup = {}
    for log in chunk:
        ssb_id = str(log.get("id", ""))
        if ssb_id:
            id_lookup[ssb_id] = log
        ts = str(log.get("timestamp", ""))
        if ts:
            ts_lookup[ts] = log

    for event in events:
        log_ids = event.get("log_ids", [])
        raw_logs = []
        for lid in log_ids[:max_logs]:
            lid_str = str(lid)
            original = id_lookup.get(lid_str) or ts_lookup.get(lid_str)
            if original:
                raw_logs.append(
                    {
                        "id": original.get("id", ""),
                        "timestamp": original.get("timestamp"),
                        "host": original.get("host", ""),
                        "program": original.get("program", ""),
                        "message": original.get("message", ""),
                    }
                )
        event["logs"] = raw_logs


def _override_match_keys(
    events: list[dict],
    key_lookup: dict[str, str],
    summary_key_lookup: dict[str, str] | None = None,
) -> None:
    """
    用程式產的 match_key 覆蓋 Haiku 的。

    兩種來源：
    1. key_lookup：從 raw log 的 dynamic_columns 產的 {ssb_id: group_key}
    2. summary_key_lookup：從預彙總摘要的 representative_log_ids 產的 {ssb_id: group_key}

    邏輯：先從 log_ids 找 raw log 的 key，找不到就找 summary 的 key，取出現最多的那個。
    """
    combined_lookup = dict(key_lookup)
    if summary_key_lookup:
        combined_lookup.update(summary_key_lookup)

    for event in events:
        log_ids = event.get("log_ids", [])
        key_counts: dict[str, int] = defaultdict(int)
        for lid in log_ids:
            key = combined_lookup.get(str(lid))
            if key:
                key_counts[key] += 1
        if key_counts:
            best_key = max(key_counts, key=key_counts.get)
            event["match_key"] = best_key


def _process_chunk(
    db,
    batch: LogBatch,
    chunk_index: int,
    chunk: list[dict],
    raw_logs: list[dict] | None = None,
    summary_key_lookup: dict[str, str] | None = None,
) -> list[dict] | None:
    """送單一 chunk 給 Claude Haiku，回傳事件 list（含原始 log 溯源 + 程式產的 match_key）。

    Args:
        chunk: 送 AI 的資料（可能含 FortiGate 彙總摘要 + Windows 精簡 log）
        raw_logs: 原始 SSB log（用於 attach raw logs 溯源），若 None 則用 chunk
        summary_key_lookup: 從預彙總摘要建的 {representative_log_id: group_key}
    """
    flash_result = FlashResult(
        batch_id=batch.id,
        chunk_index=chunk_index,
        chunk_size=len(chunk),
        status="pending",
    )
    db.add(flash_result)
    db.commit()

    lookup_source = raw_logs if raw_logs else chunk
    key_lookup = _build_key_lookup(lookup_source)

    for attempt in range(settings.FLASH_MAX_RETRY):
        try:
            if attempt > 0:
                wait = 65 * (attempt + 1)
                logger.info(
                    f"chunk {chunk_index} retry {attempt + 1}, waiting {wait}s for rate limit..."
                )
                time.sleep(wait)
            events = analyze_chunk(chunk)
            _override_match_keys(events, key_lookup, summary_key_lookup)
            _attach_raw_logs(events, lookup_source)
            flash_result.events = events
            flash_result.status = "success"
            flash_result.processed_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"chunk {chunk_index} success, found {len(events)} events")
            return events
        except Exception as exc:
            logger.warning(f"chunk {chunk_index} attempt {attempt + 1} failed: {exc}")

    flash_result.status = "failed"
    flash_result.error_message = f"Exceeded max retries {settings.FLASH_MAX_RETRY}"
    db.commit()
    logger.error(f"chunk {chunk_index} final failure")
    return None


def _process_ingest(db, payload: IngestPayload) -> dict:
    """
    處理 adapter 送來的 ingest payload：建立 LogBatch → 切 chunk → Haiku 分析 → 合併 → 更新累計。

    Returns:
        {"batch_id": int, "events_merged": int}
    """
    batch = LogBatch(
        time_from=payload.time_from,
        time_to=payload.time_to,
        records_fetched=payload.records_fetched,
        status="running",
    )
    db.add(batch)
    db.commit()

    try:
        logs = payload.logs
        analysis_mode = payload.analysis_mode

        # full 模式下 payload.logs 已含 FortiGate 彙總摘要（由 adapter 預彙總）
        # 從摘要建立 {representative_log_id: group_key} lookup
        summary_key_lookup = None
        if analysis_mode == "full":
            summary_key_lookup = _build_summary_key_lookup(logs)

        # windows_only 模式下 log 量小，不需要切 chunk
        if analysis_mode == "windows_only":
            chunks = [logs] if logs else []
        else:
            chunks = [
                logs[i : i + settings.FLASH_CHUNK_SIZE]
                for i in range(0, max(len(logs), 1), settings.FLASH_CHUNK_SIZE)
            ]
        batch.chunks_total = len(chunks)
        db.commit()

        all_chunk_events = []
        for idx, chunk in enumerate(chunks):
            events = _process_chunk(
                db,
                batch,
                chunk_index=idx,
                chunk=chunk,
                summary_key_lookup=summary_key_lookup,
            )
            if events:
                all_chunk_events.extend(events)
            batch.chunks_done = idx + 1
            db.commit()

        batch_merged = _merge_events(all_chunk_events)
        logger.info(
            f"Batch id={batch.id}: {len(all_chunk_events)} raw events → {len(batch_merged)} merged events"
        )

        if batch_merged:
            merged_result = FlashResult(
                batch_id=batch.id,
                chunk_index=999,
                chunk_size=payload.records_fetched,
                events=batch_merged,
                status="success",
                processed_at=datetime.now(timezone.utc),
            )
            db.add(merged_result)
            db.commit()

            _update_daily_accumulator(db, payload.time_to.date(), batch_merged)

        batch.status = "success"

    except Exception as exc:
        batch.status = "failed"
        batch.error_message = str(exc)
        logger.exception(f"Batch id={batch.id} failed: {exc}")

    finally:
        db.commit()

    return {
        "batch_id": batch.id,
        "events_merged": len(batch_merged) if batch_merged else 0,
    }
