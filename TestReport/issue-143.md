# TestReport：[SD] 使用者管理頁面新增停用/啟用帳號功能

## 工作項目

**⚠️ ── AI 填寫開始，請逐行審查 ──**

| # | 類型 | 工作內容 | 參照規格 | PG執行註記 |
|---|------|--------|--------| --- |
| 1 | 畫面 | 調整 `fn_user_01_list`：清單表格新增「**狀態**」欄位，並在「執行動作」欄新增狀態切換按鈕 | `SD/sdSpec/fn_user/fn_user_01_list.md` |  |
| 2 | API | 建立 `fn_user_toggle_api`：切換使用者帳號啟用/停用狀態 | `SD/sdSpec/fn_user/Api/fn_user_toggle_api.md` |  |
| 3 | API | 調整 `fn_auth_01_login_api`：停用帳號嘗試登入時回傳獨立訊息「帳號已停用，請聯絡系統管理員」 | `SD/sdSpec/fn_auth/Api/fn_auth_01_login_api.md` |  |
| 4 | Test | 更新 `fn_user` API 測試規格（新增 toggle API 測試案例） | `SD/sdSpec/fn_user/Api/_fn_user_test_api.md` |  |
| 5 | Test | 建立 `fn_auth` API 測試規格（涵蓋 login 成功與停用帳號失敗案例） | `SD/sdSpec/fn_auth/Api/_fn_auth_test_api.md` |  |

**── AI 填寫結束 ──**

## 測試案例

**⚠️ ── AI 填寫開始，請逐行審查 ──**

| ID | 類型 | 前置條件 | 操作 | 預期結果 | PG執行註記 |
|----|------|--------|------|--------| --- |
| T1 | 畫面 | 已登入且具備 fn_user 功能權限，使用者清單含啟用與停用帳號各至少 1 筆 | 進入帳號管理查詢畫面 | 清單顯示「**狀態**」欄位；啟用帳號顯示綠色「啟用」標記與「停用」按鈕；停用帳號顯示灰色「停用」標記與「啟用」按鈕 |  |
| T2 | API | 已登入且具備 fn_user 功能權限，目標帳號目前為「啟用（is_active=true）」 | PATCH /api/user/{email}/toggle | 200 狀態更新成功；tb_users.is_active 變為 false |  |
| T3 | API | 已登入且具備 fn_user 功能權限，目標帳號目前為「停用（is_active=false）」 | PATCH /api/user/{email}/toggle | 200 狀態更新成功；tb_users.is_active 變為 true |  |
| T4 | API | 已登入且具備 fn_user 功能權限 | PATCH /api/user/notexist@example.com/toggle | 404 使用者不存在 |  |
| T5 | API | 已登入但使用者角色不具備 fn_user 功能權限 | PATCH /api/user/{email}/toggle | 403 您沒有執行此操作的權限 |  |
| T6 | API | 目標帳號 is_active=false，直接嘗試登入 | POST /auth/login，傳入停用帳號的帳號與正確密碼 | 401，message 為「帳號已停用，請聯絡系統管理員」 |  |
| T7 | API | 帳號與密碼正確，且帳號 is_active=true | POST /auth/login，傳入正確帳號與密碼 | 200，回傳 access_token 與 token_type |  |
| T8 | 畫面 | 已登入且具備 fn_user 功能權限，目標帳號目前為「啟用」 | 點擊目標帳號列的「停用」按鈕，確認提示後確認 | 狀態欄更新為「停用」，操作欄按鈕變更為「啟用」 |  |
| T9 | 畫面 | 已登入且具備 fn_user 功能權限，目標帳號目前為「停用」 | 點擊目標帳號列的「啟用」按鈕，確認提示後確認 | 狀態欄更新為「啟用」，操作欄按鈕變更為「停用」 |  |

**── AI 填寫結束 ──**

---

## 設計決定

**⚠️ ── AI 填寫開始，請逐行審查 ──**

1. **toggle API 設計**：採用 `PATCH /api/user/{email}/toggle` 而非傳入 `is_active` 欄位，理由是切換操作語意更明確，避免前端誤傳任意值。
2. **登入失敗訊息區分**：停用帳號嘗試登入時，回傳獨立訊息「帳號已停用，請聯絡系統管理員」，而非與帳號/密碼錯誤合併，理由是業務需求明確要求用戶知道帳號停用的原因，有助引導聯絡管理員，且停用狀態本身不構成安全洩漏（攻擊者若知道帳號存在也無法登入）。

**── AI 填寫結束 ──**
