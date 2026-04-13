# TestReport：[SD] Workflow Issue Body 精簡測試

## 本次工作範圍
| # | 類型 | 說明 |  |  |
|---|------|------| --- | --- |
| 1 | API  | GET /api/health — 系統健康檢查端點 |  |  |
| 2 | API  | GET /api/workflow/status — 取得 workflow 狀態 |  |  |

## 測試案例
| ID | 類型 | 前置條件 | 操作 | 預期結果 |  |  |
|----|------|---------|------|---------| --- | --- |
| T1 | API  | 服務正常運行 | GET /api/health | 200 OK，回傳 `{"status": "ok"}` |  |  |
| T2 | API  | 服務正常運行 | GET /api/workflow/status | 200 OK，回傳 workflow 狀態物件 |  |  |
| T3 | API  | 傳入無效 query param | GET /api/workflow/status?format=invalid | 400 Bad Request |  |  |

> 最低要求：每個 API 至少一個成功案例（2xx）+ 一個失敗案例（4xx/5xx）；每個畫面至少一個主流程案例
