# TestReport：[SD] 實作[使用者]維護功能

## 工作項目

| # | 類型 | 工作內容 | 參照規格 | PG執行註記 |
|---|------|--------|--------| --- |
| 1 | Schema | 建立 tb_users、tb_user_roles | [schema/schema.md](../schema/schema.md) | 已確認 User/Role/UserRole model 存在；補充 updated_by FK 欄位至 User |
| 2 | API | 建立 fn_user_query_api | [Spec/fn_user/Api/fn_user_query_api.md](../Spec/fn_user/Api/fn_user_query_api.md) | GET /api/users，支援 role_id / keyword 過濾，需 can_manage_accounts 權限 |
| 3 | API | 建立 fn_user_add_api | [Spec/fn_user/Api/fn_user_add_api.md](../Spec/fn_user/Api/fn_user_add_api.md) | POST /api/users，bcrypt hash 密碼，逐筆寫入 user_roles |
| 4 | API | 建立 fn_user_update_api | [Spec/fn_user/Api/fn_user_update_api.md](../Spec/fn_user/Api/fn_user_update_api.md) | PATCH /api/users/{email}，支援選擇性更新 name/password/roles |
| 5 | API | 建立 fn_user_del_api | [Spec/fn_user/Api/fn_user_del_api.md](../Spec/fn_user/Api/fn_user_del_api.md) | DELETE /api/users/{email}，防止自我刪除，先刪 user_roles 再刪 user |
| 6 | 畫面 | 建立 fn_user_01_list | [Spec/fn_user/fn_user_01_list.md](../Spec/fn_user/fn_user_01_list.md) | 前端範圍，後端不處理 |
| 7 | 畫面 | 建立 fn_user_02_form | [Spec/fn_user/fn_user_02_form.md](../Spec/fn_user/fn_user_02_form.md) | 前端範圍，後端不處理 |
| 8 | Test | 建立 _fn_user_test_api.md | [Spec/fn_user/Api/_fn_user_test_api.md](../Spec/fn_user/Api/_fn_user_test_api.md) | 20 個 pytest 測試案例涵蓋 T1-T13，全數通過 |
| 9 | API | 建立 fn_role_options_api | [Spec/fn_role/Api/fn_role_options_api.md](../Spec/fn_role/Api/fn_role_options_api.md) | GET /api/roles/options，只需登入，依名稱升冪排序 |

## 測試結果

| 測試案例 | 對應 TestSpec ID | 結果 |
|----------|-----------------|------|
| test_list_users_returns_200 | T1 | PASS |
| test_list_users_no_permission_returns_403 | T2 | PASS |
| test_list_users_unauthenticated_returns_401 | - | PASS |
| test_list_users_filter_by_role | T11 | PASS |
| test_list_users_filter_by_keyword | T12 | PASS |
| test_create_user_returns_201 | T3 | PASS |
| test_create_user_duplicate_email_returns_400 | T4 | PASS |
| test_create_user_short_password_returns_400 | T5 | PASS |
| test_create_user_empty_roles_returns_400 | T6 | PASS |
| test_create_user_unauthenticated_returns_401 | - | PASS |
| test_update_user_returns_200 | T7 | PASS |
| test_update_user_not_found_returns_404 | T8 | PASS |
| test_update_user_short_password_returns_400 | T13 | PASS |
| test_update_user_unauthenticated_returns_401 | - | PASS |
| test_delete_user_returns_200 | T9 | PASS |
| test_delete_self_returns_400 | T10 | PASS |
| test_delete_user_not_found_returns_404 | - | PASS |
| test_delete_user_unauthenticated_returns_401 | - | PASS |
| test_get_role_options_returns_200 | - | PASS |
| test_get_role_options_unauthenticated_returns_401 | - | PASS |

**總計：20 passed，0 failed**

## 備註

- 全局測試（含既有 test_ingest、test_migration_seed）共 27 個，全數通過，無回歸問題。
- conftest.py 補充建立 `token_blacklist` 表，因 `get_current_user` deps 需查此表。
- 表格命名沿用現有慣例（無 `tb_` 前綴）：`users`、`roles`、`user_roles`。
