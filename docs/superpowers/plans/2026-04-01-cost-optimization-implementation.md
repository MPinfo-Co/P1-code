# 成本優化實作紀錄

> 日期：2026-04-01
> 設計文件：`docs/superpowers/specs/2026-04-01-cost-optimization-design.md`

## 實作方式

兩個方案由 subagent 在獨立 git worktree 中平行開發，互不影響。

---

## 方案 A：純 Windows（branch: feature/cost-opt-windows-only）

### 修改的檔案

| 檔案 | 改動說明 |
|------|---------|
| `backend/app/core/config.py` | 新增 `ANALYSIS_MODE`（預設 "windows_only"）、`SSB_SEARCH_EXPRESSION_WINDOWS_ONLY`（12 個 EventID）、`effective_search_expression` property |
| `backend/app/services/claude_flash.py` | 新增 `_slim_log_windows()`：從 dynamic_columns 取 5 個結構化欄位 + 精簡 message（砍掉尾巴固定說明）。新增 Windows 專用 prompt |
| `backend/app/tasks/flash_task.py` | 使用 `effective_search_expression`；windows_only 模式不切 chunk（~100 筆一次送） |
| `backend/scripts/run_pipeline.py` | 同步使用 effective_search_expression + windows_only chunk 邏輯 |
| `backend/tests/tasks/test_flash_task.py` | 拆分測試為 full_mode 和 windows_only_mode 兩個 |

### Windows 動態欄位（從 dynamic_columns 取）
- event_id, event_username, event_host, event_type, event_category

### Windows EventID（12 個）
- 原有：4625, 4648, 4720, 4722, 4725, 4740
- 新增：4719, 4726, 4728, 4732, 4756, 1102

### Message 精簡方式
- 用 regex 砍掉每筆 message 尾巴的固定說明文字（「當...的時候，就會產生這個事件」開頭的段落）

---

## 方案 B：Windows + FortiGate 精簡版（branch: feature/cost-opt-full）

### 修改的檔案

| 檔案 | 改動說明 |
|------|---------|
| `backend/app/core/config.py` | 新增 `ANALYSIS_MODE`（預設 "full"）、`SSB_SEARCH_EXPRESSION_WINDOWS_ONLY`、`effective_search_expression` property |
| `backend/app/services/claude_flash.py` | `_slim_log()` 改為分類處理：FortiGate 用動態欄位不送 message、Windows 動態欄位+精簡 message、未知類型用舊邏輯 fallback。更新 prompt 描述兩種格式 |
| `backend/app/services/log_preaggregator.py` | **新增**。FortiGate 預彙總模組：deny 外部按 dstip 前三段分組、deny 內部按 srcip 分組、warning 按 subtype 分組。回傳 (forti_summaries, windows_logs) |
| `backend/app/tasks/flash_task.py` | 整合 preaggregator：full 模式下送 AI 前先彙總，raw_logs 另外傳遞供溯源 |
| `backend/scripts/run_pipeline.py` | 同步整合 preaggregator |

### FortiGate 動態欄位（從 dynamic_columns 取，不送 message）
- action, level, subtype, srcip, dstip, dstport, srccountry, service

### FortiGate 預彙總邏輯
- deny 外部（srcip 非 RFC1918）：group by dstip 前三段 → 輸出 target_subnet, total_count, unique_src_ips, top_dst_ports, src_countries
- deny 內部（srcip 為 RFC1918）：group by srcip → 輸出 srcip, total_count, dst_ips, top_dst_ports
- warning：group by subtype → 輸出 subtype, total_count, top_src_ips, top_dst_ips, top_dst_ports

### 設計決策
- `_is_external_ip()` 在 preaggregator 中複製了一份，避免與 flash_task 的循環 import
- AI 收到的是彙總摘要，但 raw_logs 另外傳遞確保溯源功能正常

---

## 合併結果

最終在 master 上合併了方案 B + 方案 A 的 windows_only 優化：
- 方案 B 的所有改動（dynamic_columns、preaggregator、prompt 更新）
- 方案 A 的 windows_only 不切 chunk 邏輯
- `flash_task.py` 使用 `settings.effective_search_expression`（不是寫死的 SSB_SEARCH_EXPRESSION）
- 12 個測試全過

## 如何切換方案

兩個方案共用 `ANALYSIS_MODE` 設定：
- `.env` 設 `ANALYSIS_MODE=windows_only` → 方案 A 行為（只分析 Windows，不切 chunk）
- `.env` 設 `ANALYSIS_MODE=full` → 方案 B 行為（Windows + FortiGate 預彙總）

方案 B 是方案 A 的超集，包含所有方案 A 的改動。
