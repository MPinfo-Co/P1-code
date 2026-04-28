# TestReport：[SD] Echo API

## 工作項目

**⚠️ ── AI 填寫開始，請逐行審查 ──**

| # | 類型 | 工作內容 | 參照規格 | PG執行註記 |
|---|------|--------|--------| --- |
| 1 | API  | 建立 `GET /echo`：接收 Query Parameter `message`（string，必填），回傳 JSON `{ "message": "ok", "data": { "message": "<輸入值>" } }` | `Spec/echo/Api/echo_get_api.md` |  |
| 2 | Test | 撰寫 `/echo` 端點自動化測試案例 | `Spec/echo/Api/echo_get_api.md` |  |

**── AI 填寫結束 ──**

## 測試案例

**⚠️ ── AI 填寫開始，請逐行審查 ──**

| ID | 類型 | 前置條件 | 操作 | 預期結果 | PG執行註記 |
|----|------|--------|------|--------| --- |
| T1 | API  | 服務正常運行 | `GET /echo?message=hello` | HTTP 200；body `{ "message": "ok", "data": { "message": "hello" } }` |  |
| T2 | API  | 服務正常運行 | `GET /echo`（未傳入 `message` 參數） | HTTP 422；body 包含參數驗證錯誤訊息 |  |

**── AI 填寫結束 ──**
