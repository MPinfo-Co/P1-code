# TestReport：[SD] 使用admin帳號首次登入環境，遭遇密碼錯誤(需確認遷移程式正確性)

## 測試案例

| ID | 類型 | 前置條件 | 操作 | 預期結果 |  |  |
|----|------|---------|------|---------| --- | --- |
| T1 | API 成功 | Migration 已執行，DB 中存在 admin 帳號 | POST /api/auth/login `{ "email": "admin@mpinfo.com.tw", "password": "admin123" }` | 200 OK，回傳 `{ "access_token": "<jwt_token>" }` |  |  |
| T2 | API 失敗 | Migration 已執行，DB 中存在 admin 帳號 | POST /api/auth/login `{ "email": "admin@mpinfo.com.tw", "password": "wrongpassword" }` | 401 Unauthorized，`{ "detail": "帳號或密碼錯誤" }` |  |  |
| T3 | 冪等驗證 | Migration 已執行一次 | 重複執行 migration upgrade function | 不拋出例外；roles 表中 admin / user 各只有一筆；users 表中 admin@mpinfo.com.tw 只有一筆 |  |  |

> 最低要求：每個 API 至少一個成功案例（2xx）+ 一個失敗案例（4xx/5xx）；每個畫面至少一個主流程案例
