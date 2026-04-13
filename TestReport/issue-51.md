# TestReport：[SD] Issue Body 結構優化驗證

## 本次工作範圍
| # | 類型 | 說明 |  |  |
|---|------|------| --- | --- |
| 1 | API  | GET /api/ping — 連線測試端點 |  |  |
| 2 | API  | GET /api/version — 取得版本資訊 |  |  |

## 測試案例
| ID | 類型 | 前置條件 | 操作 | 預期結果 |  |  |
|----|------|---------|------|---------| --- | --- |
| T1 | API  | 服務正常運行 | GET /api/ping | 200 OK，回傳 `{"pong": true}` |  |  |
| T2 | API  | 服務正常運行 | GET /api/version | 200 OK，回傳版本物件 |  |  |
| T3 | API  | 傳入不存在路徑 | GET /api/version/unknown | 404 Not Found |  |  |

> 最低要求：每個 API 至少一個成功案例（2xx）+ 一個失敗案例（4xx/5xx）；每個畫面至少一個主流程案例
