# TestReport：[SD] 實作「角色」功能

## 工作項目

| #  | 類型   | 工作內容                                                                              | 參照規格                                      | PG執行註記 |
| -- | ---- | --------------------------------------------------------------------------------- | ----------------------------------------- | --- |
| 1  | Schema | 調整 `tb_roles`：移除所有 `can_*` 欄位                                                   | schema/schema.md                          |  |
| 2  | Schema | 移除 `tb_role_ai_partners`、`tb_role_kb_map`                                        | schema/schema.md                          |  |
| 3  | Schema | 建立 `tb_functions`（function_id, function_name），初始資料：fn_user、fn_role              | schema/schema.md                          |  |
| 4  | Schema | 建立 `tb_role_function`（role_id FK → tb_roles, function_id FK → tb_functions）      | schema/schema.md                          |  |
| 5  | 其他   | 調整 `Role` model：移除 `can_*` 欄位；建立 `Function` model、`RoleFunction` model          | schema/schema.md                          |  |
| 6  | 其他   | 建立 Alembic migration：對應 #1–#4 schema 變更                                          | schema/schema.md                          |  |
| 7  | 其他   | Alembic migration seed data：寫入 tb_functions 兩筆初始資料（fn_user、fn_role）              | schema/schema.md                          |  |
| 8  | API  | 調整 fn_role_query_api：傳回結果新增 `functions[]`                                        | Spec/fn_role/Api/fn_role_query_api.md     |  |
| 9  | API  | 調整 fn_role_add_api：傳入參數改為 `function_ids: integer[]`；執行寫入 `tb_role_function`      | Spec/fn_role/Api/fn_role_add_api.md       |  |
| 10 | API  | 調整 fn_role_update_api：同上                                                          | Spec/fn_role/Api/fn_role_update_api.md    |  |
| 11 | API  | 調整 fn_role_del_api：執行補上刪除 `tb_role_function`                                     | Spec/fn_role/Api/fn_role_del_api.md       |  |
| 12 | API  | 調整 fn_user_query_api：權限檢核改為查 `tb_role_function`（function_name = fn_user）         | Spec/fn_user/Api/fn_user_query_api.md     |  |
| 13 | API  | 調整 fn_user_add_api：同上                                                             | Spec/fn_user/Api/fn_user_add_api.md       |  |
| 14 | API  | 調整 fn_user_update_api：同上                                                          | Spec/fn_user/Api/fn_user_update_api.md    |  |
| 15 | API  | 調整 fn_user_del_api：同上                                                             | Spec/fn_user/Api/fn_user_del_api.md       |  |
| 16 | 畫面   | 確認 fn_role_01_list：角色清單畫面（關鍵字篩選、角色名稱、使用者欄位、修改／刪除按鈕）                             | Spec/fn_role/fn_role_01_list.md           |  |
| 17 | 畫面   | 確認 fn_role_02_form：角色表單畫面（角色名稱、成員、功能權限：使用者管理／角色管理）                               | Spec/fn_role/fn_role_02_form.md           |  |
| 18 | Test | 確認 fn_role API 測試規格檔案完整                                                          | Spec/fn_role/Api/_fn_role_test_api.md     |  |
| 19 | API  | 建立 fn_user_options_api：GET /api/users/options 輕量選項清單（供角色管理成員選擇使用）            | Spec/fn_user/Api/fn_user_options_api.md   |  |
| 20 | API  | 建立 fn_function_options_api：GET /api/functions/options 輕量選項清單（供角色管理功能權限選擇使用） | Spec/fn_role/Api/fn_function_options_api.md |  |


## 測試案例


| ID | 類型 | 前置條件 | 操作 | 預期結果 | PG執行註記 |
|----|------|--------|------|--------| --- |
| T1 | API | 已登入且使用者角色具備 fn_role 功能權限，DB 有多筆角色 | GET /api/roles | 200，data 包含每筆角色名稱、使用者陣列及 functions 陣列 |  |
| T2 | API | 已登入但使用者角色不具備 fn_role 功能權限 | GET /api/roles | 403 您沒有執行此操作的權限 |  |
| T3 | API | 已登入且使用者角色具備 fn_role 功能權限，DB 有名稱含「管理員」的角色 | GET /api/roles?keyword=管理員 | 200，data 只包含名稱含「管理員」的角色 |  |
| T4 | API | 已登入且使用者角色具備 fn_role 功能權限，角色名稱「測試角色」不存在 | POST /api/roles，傳入有效角色名稱「測試角色」 | 201 新增成功 |  |
| T5 | API | 已登入且使用者角色具備 fn_role 功能權限，角色名稱「測試角色」已存在 | POST /api/roles，傳入角色名稱「測試角色」 | 400 此角色名稱已存在 |  |
| T6 | API | 已登入且使用者角色具備 fn_role 功能權限 | POST /api/roles，角色名稱傳入空字串 | 400 角色名稱未填寫 |  |
| T7 | API | 已登入且使用者角色具備 fn_role 功能權限，角色「測試角色」存在 | PATCH /api/roles/測試角色，傳入新角色名稱「修改後角色」 | 200 更新成功 |  |
| T8 | API | 已登入且使用者角色具備 fn_role 功能權限 | PATCH /api/roles/不存在的角色，傳入任意名稱 | 404 角色不存在 |  |
| T9 | API | 已登入且使用者角色具備 fn_role 功能權限，「角色A」「角色B」均存在 | PATCH /api/roles/角色A，角色名稱傳入「角色B」 | 400 此角色名稱已被其他角色使用 |  |
| T10 | API | 已登入且使用者角色具備 fn_role 功能權限，角色「待刪角色」存在 | DELETE /api/roles/待刪角色 | 200 刪除成功，tb_roles 及關聯資料表（tb_user_roles、tb_role_function）對應紀錄移除 |  |
| T11 | API | 已登入且使用者角色具備 fn_role 功能權限 | DELETE /api/roles/不存在的角色 | 404 角色不存在 |  |
| T12 | 畫面 | 已登入且使用者角色具備 fn_role 功能權限，清單有多筆角色 | 開啟角色清單畫面 → 輸入關鍵字 → 點擊 [套用] | 清單僅顯示角色名稱含關鍵字的筆數，無法匹配時顯示空清單 |  |
| T13 | 畫面 | 已登入且使用者角色具備 fn_role 功能權限 | 點擊 [新增角色] → 填入角色名稱 → 勾選成員與功能權限 → 點擊 [儲存] | 表單關閉，清單刷新，新角色出現於清單末尾 |  |
| T14 | 畫面 | 已登入且使用者角色具備 fn_role 功能權限，清單有角色資料 | 點擊某角色的 [修改] → 修改角色名稱 → 點擊 [儲存] | 表單帶入原有資料（含成員、功能權限勾選狀態）；儲存後表單關閉，清單刷新，角色名稱已更新 |  |
| T15 | 畫面 | 已登入且使用者角色具備 fn_role 功能權限，清單有角色資料 | 點擊某角色的 [刪除] → 確認提示彈出 → 點擊 [確認刪除] | 清單中該角色移除；點擊 [取消] 則關閉提示，清單不變 |  |
| T16 | API  | 已登入 | GET /api/users/options | 200，data 為 `[{ id, name }]` 陣列，只含 is_active = true 的使用者 |  |
| T17 | API  | 未登入 | GET /api/users/options | 401 未登入或 Token 過期 |  |
| T18 | API  | 已登入 | GET /api/functions/options | 200，data 為 `[{ function_id, function_name }]` 陣列 |  |
| T19 | API  | 未登入 | GET /api/functions/options | 401 未登入或 Token 過期 |  |

**── AI 填寫結束 ──**
