"""
FortiGate log 預彙總模組。

在送 AI 分析之前，將大量重複的 FortiGate log 彙總成摘要，
大幅降低 token 用量。Windows log 不做彙總，原樣通過。

典型效果：~1,500 筆 FortiGate → ~20-50 筆摘要
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


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


_FORTI_PREFIX = ".sdata.forti."
_WIN_PREFIX = ".sdata.win@18372.4."


def _get_forti_field(log: dict, field: str) -> str:
    """從 dynamic_columns 取 FortiGate 欄位。"""
    return log.get("dynamic_columns", {}).get(f"{_FORTI_PREFIX}{field}", "")


def _is_forti_log(log: dict) -> bool:
    dc = log.get("dynamic_columns", {})
    return any(k.startswith(_FORTI_PREFIX) for k in dc)


def _is_windows_log(log: dict) -> bool:
    dc = log.get("dynamic_columns", {})
    return any(k.startswith(_WIN_PREFIX) for k in dc)


def _format_time_range(timestamps: list[int | float]) -> str:
    """將 unix timestamp 列表轉為 HH:MM~HH:MM 格式。"""
    if not timestamps:
        return ""
    ts_min = min(timestamps)
    ts_max = max(timestamps)
    t_from = datetime.fromtimestamp(ts_min, tz=timezone.utc).strftime("%H:%M")
    t_to = datetime.fromtimestamp(ts_max, tz=timezone.utc).strftime("%H:%M")
    return f"{t_from}~{t_to}"


def _top_n(counter: dict, n: int = 5) -> list:
    """取 counter 中出現次數最多的前 n 個 key。"""
    return [k for k, _ in sorted(counter.items(), key=lambda x: -x[1])[:n]]


def _pick_representative_ids(logs: list[dict], n: int = 5) -> list[str]:
    """從一組 log 中取最多 n 筆的 SSB ID，供溯源用。"""
    ids = []
    for log in logs[:n]:
        ssb_id = log.get("id")
        if ssb_id:
            ids.append(str(ssb_id))
    return ids


def _aggregate_deny_external(logs: list[dict]) -> list[dict]:
    """deny 外部來源：Group by dstip 前三段。"""
    groups: dict[str, list[dict]] = defaultdict(list)
    for log in logs:
        dstip = _get_forti_field(log, "dstip") or "unknown"
        subnet = ".".join(dstip.split(".")[:3])
        groups[subnet].append(log)

    summaries = []
    for subnet, group_logs in groups.items():
        src_ips: dict[str, int] = defaultdict(int)
        dst_ports: dict[str, int] = defaultdict(int)
        countries: dict[str, int] = defaultdict(int)
        timestamps = []

        for log in group_logs:
            srcip = _get_forti_field(log, "srcip")
            if srcip:
                src_ips[srcip] += 1
            dstport = _get_forti_field(log, "dstport")
            if dstport:
                dst_ports[dstport] += 1
            country = _get_forti_field(log, "srccountry")
            if country:
                countries[country] += 1
            ts = log.get("timestamp")
            if ts:
                timestamps.append(ts)

        summaries.append(
            {
                "type": "deny_external",
                "group_key": f"deny_external_{subnet}",
                "target_subnet": f"{subnet}.0/24",
                "total_count": len(group_logs),
                "unique_src_count": len(src_ips),
                "top_src_ips": _top_n(src_ips, 10),
                "top_dst_ports": _top_n(dst_ports),
                "src_countries": _top_n(countries, 10),
                "time_range": _format_time_range(timestamps),
                "representative_log_ids": _pick_representative_ids(group_logs),
            }
        )

    return summaries


def _aggregate_deny_internal(logs: list[dict]) -> list[dict]:
    """deny 內部來源：Group by srcip。"""
    groups: dict[str, list[dict]] = defaultdict(list)
    for log in logs:
        srcip = _get_forti_field(log, "srcip") or "unknown"
        groups[srcip].append(log)

    summaries = []
    for srcip, group_logs in groups.items():
        dst_ips: dict[str, int] = defaultdict(int)
        dst_ports: dict[str, int] = defaultdict(int)
        timestamps = []

        for log in group_logs:
            dstip = _get_forti_field(log, "dstip")
            if dstip:
                dst_ips[dstip] += 1
            dstport = _get_forti_field(log, "dstport")
            if dstport:
                dst_ports[dstport] += 1
            ts = log.get("timestamp")
            if ts:
                timestamps.append(ts)

        summaries.append(
            {
                "type": "deny_internal",
                "group_key": f"deny_internal_{srcip}",
                "srcip": srcip,
                "total_count": len(group_logs),
                "dst_ips": _top_n(dst_ips, 10),
                "top_dst_ports": _top_n(dst_ports),
                "time_range": _format_time_range(timestamps),
                "representative_log_ids": _pick_representative_ids(group_logs),
            }
        )

    return summaries


def _aggregate_warning(logs: list[dict]) -> list[dict]:
    """warning：Group by subtype。"""
    groups: dict[str, list[dict]] = defaultdict(list)
    for log in logs:
        subtype = _get_forti_field(log, "subtype") or "unknown"
        groups[subtype].append(log)

    summaries = []
    for subtype, group_logs in groups.items():
        src_ips: dict[str, int] = defaultdict(int)
        dst_ips: dict[str, int] = defaultdict(int)
        dst_ports: dict[str, int] = defaultdict(int)
        timestamps = []

        for log in group_logs:
            srcip = _get_forti_field(log, "srcip")
            if srcip:
                src_ips[srcip] += 1
            dstip = _get_forti_field(log, "dstip")
            if dstip:
                dst_ips[dstip] += 1
            dstport = _get_forti_field(log, "dstport")
            if dstport:
                dst_ports[dstport] += 1
            ts = log.get("timestamp")
            if ts:
                timestamps.append(ts)

        summaries.append(
            {
                "type": "warning",
                "group_key": f"warning_{subtype}",
                "subtype": subtype,
                "total_count": len(group_logs),
                "top_src_ips": _top_n(src_ips),
                "top_dst_ips": _top_n(dst_ips),
                "top_dst_ports": _top_n(dst_ports),
                "time_range": _format_time_range(timestamps),
                "representative_log_ids": _pick_representative_ids(group_logs),
            }
        )

    return summaries


def preaggregate(logs: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    將 log 分成 FortiGate 彙總摘要 + Windows 原始 log。

    FortiGate log 依類型（deny_external / deny_internal / warning）分組彙總，
    大幅減少送 AI 的資料量。Windows log 不做彙總，保持原樣。

    Returns:
        (forti_summaries, windows_logs)
    """
    forti_deny_external = []
    forti_deny_internal = []
    forti_warning = []
    windows_logs = []
    other_logs = []

    for log in logs:
        if _is_forti_log(log):
            action = _get_forti_field(log, "action")
            level = _get_forti_field(log, "level")
            srcip = _get_forti_field(log, "srcip")

            if action == "deny":
                if _is_external_ip(srcip):
                    forti_deny_external.append(log)
                else:
                    forti_deny_internal.append(log)
            elif level == "warning":
                forti_warning.append(log)
            else:
                # 其他 FortiGate log 也彙總到 warning（fallback）
                forti_warning.append(log)
        elif _is_windows_log(log):
            windows_logs.append(log)
        else:
            other_logs.append(log)

    forti_summaries = []
    forti_summaries.extend(_aggregate_deny_external(forti_deny_external))
    forti_summaries.extend(_aggregate_deny_internal(forti_deny_internal))
    forti_summaries.extend(_aggregate_warning(forti_warning))

    logger.info(
        f"Preaggregate: {len(logs)} logs -> "
        f"{len(forti_summaries)} FortiGate summaries + "
        f"{len(windows_logs)} Windows logs + "
        f"{len(other_logs)} other"
    )

    # other_logs 放進 windows_logs 一起送 AI
    return forti_summaries, windows_logs + other_logs
