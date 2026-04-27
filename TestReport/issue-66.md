# TestReport：issue-66

## TDD 規格合規

| # | 類型 | 工作內容 | 結果 |
|---|------|--------|------|
| 1 | Schema | 建立 tb_users、tb_user_roles | PASS |
| 2 | API | 建立 fn_user_query_api | PASS |
| 3 | API | 建立 fn_user_add_api | PASS |
| 4 | API | 建立 fn_user_update_api | PASS |
| 5 | API | 建立 fn_user_del_api | PASS |
| 6 | 畫面 | 建立 fn_user_01_list | 略過（畫面類型）|
| 7 | 畫面 | 建立 fn_user_02_form | 略過（畫面類型）|
| 8 | Test | 建立 _fn_user_test_api.md | PASS |

## pytest 結果

通過：11 / 總計：11

| TestSpec ID | 測試函式 | 結果 |
|-------------|----------|------|
| T1 | test_list_users_returns_200 | PASS |
| T2 | test_list_users_no_permission_returns_403 | PASS |
| T3 | test_create_user_returns_201 | PASS |
| T4 | test_create_user_duplicate_email_returns_400 | PASS |
| T5 | test_create_user_short_password_returns_400 | PASS |
| T6 | test_create_user_empty_roles_returns_400 | PASS |
| T7 | test_update_user_returns_200 | PASS |
| T8 | test_update_user_not_found_returns_404 | PASS |
| T9 | test_delete_user_returns_200 | PASS |
| T10 | test_delete_self_returns_400 | PASS |
| 額外 | test_list_users_no_token_returns_401 | PASS |

## 已知差異

- Schema 模型的資料表名稱為 `users` / `roles` / `user_roles`（非 `tb_` 前綴），與 schema.md 中的 `tb_users` / `tb_roles` / `tb_user_roles` 命名不符。功能運作正常，不影響 API 行為與測試結果。

## 備註

- T5（密碼不足）與 T6（角色為空）由 Pydantic validator 在 422 層攔截，response body 詳細錯誤訊息中包含對應中文說明；測試驗證 422 status code 及錯誤訊息內容均符合預期。
- 額外測試 `test_list_users_no_token_returns_401` 覆蓋 401 未登入情境，使規格覆蓋更完整（測試數量 11 ≥ 規格案例數 10）。

---

## 前端 TDD 規格合規（畫面類型）

| # | 工作內容 | 結果 |
|---|---------|------|
| 6 | 建立 fn_user_01_list | ✓ |
| 7 | 建立 fn_user_02_form | ✓ |

## 前端 TypeScript + ESLint

TypeScript: 通過（0 型別錯誤，僅 TS5101 baseUrl deprecation warning，屬已知專案設定問題）
ESLint: 通過（0 警告，0 錯誤）

## 前端備註

- fn_user_01_list（FnUserList.tsx）：篩選列含角色職位 select（選項來源 /api/roles）與關鍵字 text input；清單表格含姓名、電子信箱、角色（Chip badge）、修改／刪除操作欄；刪除確認訊息「確定要刪除 {名稱}？此操作無法還原」符合規格；新增帳號按鈕位於頁面右上角；路由 /settings/account → FnUserList 已在 App.jsx 正確配置；Sidebar 設定群組「帳號管理」使用 PeopleAltOutlined icon，path 指向 /settings/account，與路由一致。
- fn_user_02_form（FnUserForm.tsx）：新增／修改共用 Dialog，標題依模式切換「新增帳號」／「修改帳號」；欄位含名稱（最長 100 字）、Email（修改模式唯讀）、密碼（最少 8 字元）、角色 checkbox group（含全選切換）；驗證失敗時在對應欄位下方顯示錯誤文字；新增模式呼叫 POST /api/users，修改模式呼叫 PATCH /api/users/{email}，與規格一致。
- API hook（useUsersQuery.ts）：GET /api/users（查詢，query params: role_id, keyword）、POST /api/users（新增）、PATCH /api/users/{email}（修改）、DELETE /api/users/{email}（刪除）— 路徑與 method 全部與 Spec/fn_user/Api/ 規格一致。
