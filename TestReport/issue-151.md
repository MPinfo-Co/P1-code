# TestReport：[SD] 移除使用者管理頁面新增停用/啟用帳號功能

## 工作項目
| # | 類型 | 工作內容 | 參照規格 | PG執行註記 |
|---|------|--------|--------| --- |
| 1 | 畫面 | 調整 `fn_user_01_list.md`：移除清單表格**狀態**欄、移除[停用]/[啟用]操作按鈕及其確認邏輯；修正**角色職位** select 選項來源格式（從表格說明欄移至獨立 blockquote，指向 `../fn_role/Api/fn_role_options_api.md`） | `SD/sdSpec/fn_user/fn_user_01_list.md` | FE 範圍，跳過 |
| 2 | 畫面 | 調整 `fn_user_02_form.md`：修正**角色** checkbox group 選項來源格式（指向 `../fn_role/Api/fn_role_options_api.md`） | `SD/sdSpec/fn_user/fn_user_02_form.md` | FE 範圍，跳過 |
| 3 | API | 調整 `fn_user_query_api.md`：傳回結果移除啟用狀態（is_active）欄位 | `SD/sdSpec/fn_user/Api/fn_user_query_api.md` | 完成：UserItem schema 移除 is_active，router 回傳不含該欄位 |
| 4 | API | 刪除 toggle API（toggle 端點未實作，確認不存在） | `SD/sdSpec/fn_user/Api/fn_user_toggle_api.md` | 完成：端點從未實作，已確認不存在 |
| 5 | Schema | 移除 `tb_users.is_active` 欄位 | `SD/schema.md` | 完成：User ORM model 移除 is_active；migration `69f55dc2_remove_is_active_from_tb_users.py` 已建立 |
| 6 | 畫面 | 調整 `sdPrototype/fn_user/fn_user.html`：移除**狀態**欄、移除停用/啟用按鈕及 `toggleStatus` 函式 | `SD/sdPrototype/fn_user/fn_user.html` | FE 範圍，跳過 |
| 7 | Test | 更新 pytest：移除 is_active 相關設定，新增 is_active 不在回傳、toggle 端點 404 的測試 | `SD/sdSpec/fn_user/Api/_fn_user_test_api.md` | 完成：24 tests all passed |

## 測試案例
| ID | 類型 | 前置條件 | 操作 | 預期結果 | PG執行註記 |
|----|------|--------|------|--------| --- |
| T1 | 畫面 | 已登入且具備 fn_user 功能權限，進入使用者管理查詢畫面 | 瀏覽清單表格欄位 | 表格欄位為：名稱、電子信箱、角色、執行動作；無**狀態**欄 | FE 範圍 |
| T2 | 畫面 | 已登入且具備 fn_user 功能權限，進入使用者管理查詢畫面 | 查看每列操作區 | 操作欄只有[修改]、[刪除]按鈕，無[停用]/[啟用]按鈕 | FE 範圍 |
| T3 | 畫面 | 已登入且具備 fn_user 功能權限，進入使用者管理查詢畫面 | 開啟**角色職位**下拉選單 | 選項由 `/api/roles/options` 提供，包含「全部」預設選項及所有角色名稱 | FE 範圍 |
| T4 | API | 已登入且使用者角色具備 fn_user 功能權限 | GET /api/user | 200，data 包含每位使用者的姓名、Email、角色陣列；不含 is_active 欄位 | PASS（test_list_users_no_is_active_in_response） |
| T5 | API | 已登入但使用者角色不具備 fn_user 功能權限 | GET /api/user | 403 您沒有執行此操作的權限 | PASS（test_list_users_no_permission_returns_403） |
| T6 | API | 已登入且具備 fn_user 功能權限 | PATCH /api/user/{email}/toggle（移除後） | 404（端點不存在，已移除） | PASS（test_toggle_endpoint_not_found） |
| T7 | Schema | 執行資料庫遷移後 | 檢查 tb_users 資料表欄位 | tb_users 不含 is_active 欄位 | migration 檔案建立，需在 PostgreSQL 環境驗證 |
| T8 | 畫面 | 已登入，進入使用者管理查詢畫面 | 點擊[新增使用者]，填入有效資料後儲存 | 新使用者出現在清單，無狀態欄顯示 | FE 範圍 |

**⚠️ ── AI 填寫開始，請逐行審查 ──**

### 設計決定

- `tb_users.is_active` 欄位移除：此功能為測試用途加入，業務上不需要停用/啟用帳號機制，直接刪除欄位可降低系統複雜度。
- `fn_user_toggle_api` 整支刪除：無對應業務需求，移除可減少攻擊面，亦符合恢復至功能加入前狀態的目標。
- 查詢 API 回傳結果不再包含 `is_active`：與 Schema 移除保持一致，前端無需處理帳號狀態顯示邏輯。
- **角色職位** 選項來源改指向 `../fn_role/Api/fn_role_options_api.md`：符合 spec-guide.md 規範，選項來源應以獨立 blockquote 行標注，且指向 options API 路徑（而非資料表）；`fn_role_options_api` 已存在，無需新增工作項目。
- `fn_user_query_api.md` Query Parameter 欄標由「參數」改為「欄位」：符合 spec-guide.md 規範（`參數 / 型別` 僅適用於 Path Parameter，Query Parameter 應使用「欄位 / 型別 / 必填」）。
- `fn_user_02_form.md` 角色 checkbox group 選項來源一併修正為 blockquote 格式：與 fn_user_01_list.md 的修正邏輯一致，統一符合規範。

**── AI 填寫結束 ──**
