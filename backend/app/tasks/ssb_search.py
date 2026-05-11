"""Canonical SSB search expression — Windows AD event IDs + FortiGate deny/warning.

The exact list of event IDs is load-bearing: changes shift what the pipeline sees.
Lifted verbatim from P1-project/integrations/ssb/config.py:11-39.
"""

SSB_SEARCH_EXPRESSION = (
    # Windows AD 資安事件
    "nvpair:.sdata.win@18372.4.event_id=4625 OR "  # 登入失敗
    "nvpair:.sdata.win@18372.4.event_id=4648 OR "  # 明確憑證登入（RunAs）
    "nvpair:.sdata.win@18372.4.event_id=4720 OR "  # 新建帳號
    "nvpair:.sdata.win@18372.4.event_id=4722 OR "  # 啟用帳號
    "nvpair:.sdata.win@18372.4.event_id=4725 OR "  # 停用帳號
    "nvpair:.sdata.win@18372.4.event_id=4740 OR "  # 帳號鎖定
    "nvpair:.sdata.win@18372.4.event_id=4719 OR "  # 稽核政策變更
    "nvpair:.sdata.win@18372.4.event_id=4726 OR "  # 刪除帳號
    "nvpair:.sdata.win@18372.4.event_id=4728 OR "  # 加入全域安全群組
    "nvpair:.sdata.win@18372.4.event_id=4732 OR "  # 加入本機安全群組
    "nvpair:.sdata.win@18372.4.event_id=4756 OR "  # 加入萬用安全群組
    "nvpair:.sdata.win@18372.4.event_id=1102 OR "  # 安全日誌被清除
    # FortiGate 防火牆
    "nvpair:.sdata.forti.action=deny OR "  # 拒絕連線
    "nvpair:.sdata.forti.level=warning"    # 警告等級
)
