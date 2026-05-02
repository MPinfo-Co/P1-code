# TestReport：[SD] 系統參數設定功能

## 工作項目

**⚠️ ── AI 填寫開始，請逐行審查 ──**

| # | 類型 | 工作內容 | 參照規格 | PG執行註記 |
|---|------|--------|--------| --- |
| 1 | Schema | 建立 `tb_system_params` | `SD/schema.md` | 完成：新增 `fn_setting.py` model；同步在 `fn_user_role.py` Role 新增 `can_manage_settings` 欄位；migration 檔案 `a1b2c3d4e5f6` |
| 2 | API | 建立 `fn_setting_list_api`（查詢系統參數清單） | `SD/sdSpec/fn_setting/Api/fn_setting_list_api.md` | 完成：GET /api/settings，支援 param_type query 過濾 |
| 3 | API | 建立 `fn_setting_update_api`（更新參數值） | `SD/sdSpec/fn_setting/Api/fn_setting_update_api.md` | 完成：PATCH /api/settings/{param_code} |
| 4 | API | 建立 `fn_setting_param_type_options_api`（取得參數類型選項） | `SD/sdSpec/fn_setting/Api/fn_setting_param_type_options_api.md` | 完成：GET /api/settings/options/param-types |
| 5 | 畫面 | 建立 `fn_setting_00_overview`（功能總覽） | `SD/sdSpec/fn_setting/fn_setting_00_overview.md` | 前端範圍，本 issue 後端實作不含 |
| 6 | 畫面 | 建立 `fn_setting_01_list`（系統參數清單畫面） | `SD/sdSpec/fn_setting/fn_setting_01_list.md` | 前端範圍，本 issue 後端實作不含 |
| 7 | 畫面 | 建立 `fn_setting_02_edit`（編輯參數值 Dialog） | `SD/sdSpec/fn_setting/fn_setting_02_edit.md` | 前端範圍，本 issue 後端實作不含 |
| 8 | 畫面 | 建立 `sdPrototype/fn_setting/fn_setting.html` | `SD/sdPrototype/fn_setting/fn_setting.html` | 前端範圍，本 issue 後端實作不含 |
| 9 | 其他 | 新增 `fn_setting` 至 `functionList.md` | `SD/functionList.md` | SD 範圍，不含 |
| 10 | Test | 建立 `_fn_setting_test_api`（API 測試規格） | `SD/sdSpec/fn_setting/Api/_fn_setting_test_api.md` | 完成：pytest 11 案例，對應 T1–T10，全數通過 |

**── AI 填寫結束 ──**

## 測試案例

**⚠️ ── AI 填寫開始，請逐行審查 ──**

| ID | 類型 | 前置條件 | 操作 | 預期結果 | PG執行註記 |
|----|------|--------|------|--------| --- |
| T1 | API | 已登入且使用者角色具備 fn_setting 功能權限，DB 有多筆系統參數 | GET /api/settings | 200，data 包含每筆參數類型、參數代碼、參數值 | PASS |
| T2 | API | 已登入但使用者角色不具備 fn_setting 功能權限 | GET /api/settings | 403 您沒有執行此操作的權限 | PASS |
| T3 | API | 未登入 | GET /api/settings | 401 未登入或 Token 過期 | PASS |
| T4 | API | 已登入且具備 fn_setting 功能權限，DB 有 paramType = 'SSB連線' 的參數 | GET /api/settings?param_type=SSB連線 | 200，data 只包含 paramType 為 SSB連線 的參數 | PASS |
| T5 | API | 已登入且具備 fn_setting 功能權限，tb_system_params 中參數代碼 SESSION_TIMEOUT_MIN 存在 | PATCH /api/settings/SESSION_TIMEOUT_MIN，傳入參數值 "30" | 200 更新成功 | PASS |
| T6 | API | 已登入但使用者角色不具備 fn_setting 功能權限 | PATCH /api/settings/SESSION_TIMEOUT_MIN，傳入參數值 "30" | 403 您沒有執行此操作的權限 | PASS |
| T7 | API | 已登入且具備 fn_setting 功能權限 | PATCH /api/settings/不存在的代碼，傳入參數值 "abc" | 404 參數不存在 | PASS |
| T8 | API | 已登入且具備 fn_setting 功能權限，參數代碼 SESSION_TIMEOUT_MIN 存在 | PATCH /api/settings/SESSION_TIMEOUT_MIN，參數值傳入空字串 | 400 參數值不可為空 | PASS |
| T9 | API | 已登入且具備 fn_setting 功能權限 | GET /api/settings/options/param-types | 200，data 包含所有不重複的參數類型字串陣列 | PASS |
| T10 | API | 未登入 | GET /api/settings/options/param-types | 401 未登入或 Token 過期 | PASS |
| T11 | 畫面 | 以管理員身份登入，TB 有多筆系統參數 | 進入系統參數清單頁，點擊 [編輯]，修改參數值後點擊 [儲存] | 顯示所有參數；編輯 Modal 開啟；儲存成功後 Modal 關閉，清單更新為新值 | 前端實作待處理 |
| T12 | 畫面 | 以非管理員身份登入 | 進入系統參數清單頁 | 操作欄不顯示，[編輯] 按鈕不出現 | 前端實作待處理 |
| T13 | 畫面 | 以管理員身份登入，開啟編輯 Modal | 清空參數值欄位後點擊 [儲存] | 顯示提示「參數值不可為空」，Modal 不關閉 | 前端實作待處理 |

**── AI 填寫結束 ──**
