# TestReport：[SD] Workflow Issue Body 精簡測試

## 本次工作範圍
| # | 類型 | 說明 |
|---|------|------|
| 1 | API  | GET /api/health — 系統健康檢查端點 |
| 2 | API  | GET /api/workflow/status — 取得 workflow 狀態 |

## 測試案例
| ID | 類型 | 前置條件 | 操作 | 預期結果 | 結果 | 備註 |
|----|------|---------|------|---------|------|------|
| T1 | API  | 服務正常運行 | GET /api/health | 200 OK，回傳 `{"status": "ok"}` | ✅ Pass | |
| T2 | API  | 服務正常運行 | GET /api/workflow/status | 200 OK，回傳 workflow 狀態物件 | ✅ Pass | |
| T3 | API  | 傳入無效 query param | GET /api/workflow/status?format=invalid | 400 Bad Request | ✅ Pass | |

## 備註

本次為 workflow 端對端測試，驗證 PM→SA→SD→PG 串接流程與 Issue body 精簡後的效果。
所有 Issue body 均正確只含「關聯項目」區塊，關聯連結填入完整。
