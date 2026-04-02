# 成本優化設計 — Haiku 分析管線

> 日期：2026-04-01
> 目的：將每日 Haiku 分析成本從 ~$76/天 降至可接受範圍

## 現況問題

### 實測數據（2026-04-01）

| 指標 | 數值 |
|------|------|
| 每 10 分鐘 log 量 | ~1,400-1,800 筆 |
| chunk size | 300 筆 |
| chunks 數量 | 5-6 |
| 每 chunk input tokens | ~101,000（實測） |
| 每 chunk 費用 | ~$0.11 |
| 每次管線（5 chunks + Sonnet） | ~$0.64 |
| 每日成本（144 次） | ~$76 |
| 每月成本 | ~$2,280 |

### 成本高的根因

1. **message 欄位太長**：平均 655 字元/筆，佔 token 大宗
2. **message 與 dynamic_columns 資訊重複**：SSB 已拆好結構化欄位，但目前只送 message 給 AI
3. **FortiGate 大量重複 log**：deny/warning 佔 94.4%，同類型 log 大量重複
4. **每筆實際 ~340 tokens**，遠超原估的 100 tokens

### Log 類型分布

| 類型 | 筆數（10 分鐘） | 佔比 |
|------|-----------------|------|
| FortiGate warning (traffic) | ~1,038 | 58.6% |
| FortiGate deny (traffic) | ~634 | 35.8% |
| Windows 4648（明確憑證登入） | ~98 | 5.5% |
| Windows 4625（登入失敗） | ~1 | 0.1% |

## 兩個方案

### 方案 A：純 Windows Log

只分析 Windows 事件，不處理 FortiGate。適合先上線、快速交付。

#### 篩選範圍

**目前已有的 EventID：**

| EventID | 說明 |
|---------|------|
| 4625 | 登入失敗 |
| 4648 | 明確憑證登入（RunAs） |
| 4720 | 新建帳號 |
| 4722 | 啟用帳號 |
| 4725 | 停用帳號 |
| 4740 | 帳號鎖定 |

**建議新增（量少但重要，需與資安部門確認）：**

| EventID | 說明 | 為什麼重要 |
|---------|------|-----------|
| 4719 | 稽核政策變更 | 可能在掩蓋入侵痕跡 |
| 4726 | 刪除帳號 | 搭配 4720 新建帳號 |
| 4728 | 加入全域安全群組 | 權限提升（如加入 Domain Admins） |
| 4732 | 加入本機安全群組 | 本機層級權限提升 |
| 4756 | 加入萬用安全群組 | 萬用群組權限提升 |
| 1102 | 安全日誌被清除 | 入侵者清除 log |

**暫不建議加入（量大，增加成本）：**

| EventID | 說明 | 不加原因 |
|---------|------|---------|
| 4624 | 登入成功 | 6 小時 6 萬筆，雜訊太多 |
| 4672 | 特殊權限指派 | 量大 |
| 4768 | Kerberos TGT 請求 | 量大，偵測 Golden Ticket 可後續加 |
| 4769 | Kerberos 服務票證 | 量大，偵測 Kerberoasting 可後續加 |
| 4771 | Kerberos 預驗證失敗 | 中量，密碼噴灑偵測可後續加 |
| 4776 | NTLM 驗證 | 量大，Pass-the-Hash 偵測可後續加 |

#### 送 AI 的資料格式

**結構化欄位（從 dynamic_columns 取）：**

| 欄位 | 來源 | 說明 |
|------|------|------|
| event_id | .sdata.win@18372.4.event_id | 事件類型 |
| event_username | .sdata.win@18372.4.event_username | 涉及帳號 |
| event_host | .sdata.win@18372.4.event_host | 發生主機 |
| event_type | .sdata.win@18372.4.event_type | Success Audit / Failure Audit |
| event_category | .sdata.win@18372.4.event_category | 事件分類（Logon 等） |

**message 欄位：保留但精簡**

Windows message 包含 dynamic_columns 沒有的重要資訊：
- 4625：來源網路位址、工作站名稱、失敗原因、登入類型
- 4648：目標伺服器名稱、處理程序名稱

精簡方式：**砍掉尾巴固定說明文字**。每種 EventID 的 message 結尾都有一段固定的事件說明（以「當...的時候，就會產生這個事件」開頭），每筆都一樣，浪費 token。程式用截斷或 regex 移除。

#### 成本預估

| 指標 | 數值 |
|------|------|
| 每 10 分鐘 log 量 | ~100 筆 |
| chunks 數量 | 1（不需切 chunk） |
| 不需等 rate limit | 幾秒完成 |
| 每次費用 | ~$0.005-0.01 |
| 每日（144 次） | ~$0.72-1.44 |
| **每月** | **~$22-43** |

---

### 方案 B：Windows + FortiGate（精簡版）

Windows 處理方式同方案 A，FortiGate 加上「改用 dynamic_columns + 預彙總」。

#### FortiGate 送 AI 的欄位（從 dynamic_columns 取）

| 欄位 | 來源 | 說明 |
|------|------|------|
| action | .sdata.forti.action | deny / ip-conn 等 |
| level | .sdata.forti.level | warning / notice 等 |
| subtype | .sdata.forti.subtype | forward / local 等 |
| srcip | .sdata.forti.srcip | 來源 IP |
| dstip | .sdata.forti.dstip | 目標 IP |
| dstport | .sdata.forti.dstport | 目標埠號 |
| srccountry | .sdata.forti.srccountry | 來源國家 |
| service | .sdata.forti.service | 服務類型 |

**不送 message**，因為上述欄位已涵蓋所有分析需要的資訊。

#### FortiGate 預彙總邏輯

程式在送 AI 之前，先把大量重複的 FortiGate log 彙總成摘要：

**deny 外部來源**（srcip 為非 RFC1918）：
- Group by：dstip 前三段（同目標網段）
- 輸出一筆摘要，包含：target_subnet、total_count、unique_src_ips 清單、top_dst_ports、src_countries、time_range

**deny 內部來源**（srcip 為 RFC1918）：
- Group by：srcip
- 輸出一筆摘要，包含：srcip、total_count、dst_ips 清單、top_dst_ports、time_range

**warning**：
- Group by：subtype
- 輸出一筆摘要，包含：subtype、total_count、top_src_ips、top_dst_ips、top_dst_ports、time_range

**範例：634 筆 deny → 彙總後**

```json
{
  "type": "deny_external",
  "target_subnet": "211.21.43.0/24",
  "total_count": 520,
  "unique_src_ips": ["45.33.12.7", "103.5.8.2", "91.44.6.33"],
  "top_dst_ports": [443, 80, 22, 3389],
  "src_countries": ["China", "Russia", "Reserved"],
  "time_range": "11:40~11:50"
}
```

預估 1,672 筆 FortiGate → 彙總為 20-50 筆摘要。

#### 成本預估

| 指標 | 數值 |
|------|------|
| Windows | ~100 筆原始 |
| FortiGate | ~1,500 筆 → 彙總 ~30 筆 |
| 送 AI 總量 | ~130 筆（1 chunk） |
| 每次費用 | ~$0.01-0.02 |
| 每日（144 次） | ~$1.5-3 |
| **每月** | **~$45-90** |

#### 可移植性考量

dynamic_columns 是 SSB 特有的功能，其他客戶可能沒有。未來如需支援無 SSB 環境：
- 有 dynamic_columns → 直接用結構化欄位（效率最高）
- 無 dynamic_columns → fallback 到從 message 用 regex 提取關鍵欄位

本次先以 SSB 環境為主實作。

## 決策紀錄

1. **Windows message 不能完全丟掉**：dynamic_columns 沒有來源 IP、失敗原因、目標伺服器等細節，但可砍掉固定說明文字
2. **FortiGate message 可以完全不送**：dynamic_columns 已涵蓋所有分析欄位
3. **新 EventID 加入不影響架構設計**：只需改 SSB_SEARCH_EXPRESSION，建議與資安部門確認後再加
4. **量大的 EventID（4768/4769/4776）暫不加**：等方案穩定後再評估
5. **兩方案共用 Windows 處理邏輯**：方案 B 是方案 A 的超集
