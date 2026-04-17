# TestReport — Issue #94：非產品程式碼遷移（SSB adapter）

## 測試結果總覽

| ID | 測試案例 | 結果 |
|----|----------|------|
| T1 | POST /api/ingest — 無 INGEST_SECRET 時跳過驗證，成功回 200 | ✅ PASSED |
| T2 | POST /api/ingest — INGEST_SECRET 設定且 key 正確，成功回 200 | ✅ PASSED |
| T3 | POST /api/ingest — INGEST_SECRET 設定但 key 錯誤，回 403 | ✅ PASSED |
| T4 | POST /api/ingest — payload 格式錯誤，回 422 | ✅ PASSED |

**pytest 執行：4 passed, 0 failed**

## 測試檔案

`backend/tests/test_ingest.py`

## 手動驗證項目

| 驗證項目 | 結果 | 備註 |
|----------|------|------|
| P1-code 啟動（無 SSB import 殘留） | ✅ | `python -m app.main` 正常 |
| `ruff check backend/` | ✅ | 無 lint 錯誤 |
| SSB 相關環境變數已移除 | ✅ | config.py 僅保留 `INGEST_SECRET` |
| `ssb_client.py` / `log_preaggregator.py` 已從 P1-code 移除 | ✅ | 已搬至 P1-project/integrations/ssb/ |

## 備註

- `_process_ingest` 中呼叫 Claude API（`analyze_chunk`）的部分使用 mock，避免 CI 環境需要 API key
- 測試使用 SQLite JSONB 型別不相容問題，改以 mock DB session 方式處理
