# TestReport：[SD] 系統公告顯示功能

## 工作項目

| # | 類型 | 工作內容 | 參照規格 | PG執行註記 |
|---|------|--------|--------| --- |
| 1 | Schema | 建立 `tb_notices` | [schema/schema.md](../schema/schema.md) |  |
| 2 | Schema | 調整 `tb_functions` 初始資料：新增 `(3, fn_notice)` | [schema/schema.md](../schema/schema.md) |  |
| 3 | Schema | 調整 `tb_role_function` 初始資料：設定管理員角色擁有 `fn_notice` 權限 | [schema/schema.md](../schema/schema.md) |  |
| 4 | API | 建立 `fn_notice_list_api`（GET /api/notices，所有登入使用者） | [Spec/fn_notice/Api/fn_notice_list_api.md](../Spec/fn_notice/Api/fn_notice_list_api.md) |  |
| 5 | API | 建立 `fn_notice_add_api`（POST /api/notices，需 fn_notice 權限） | [Spec/fn_notice/Api/fn_notice_add_api.md](../Spec/fn_notice/Api/fn_notice_add_api.md) |  |
| 6 | 畫面 | 建立功能總覽 `fn_notice_00_overview.md` | [Spec/fn_notice/fn_notice_00_overview.md](../Spec/fn_notice/fn_notice_00_overview.md) |  |
| 7 | 畫面 | 建立畫面規格 `fn_notice_01_home_block.md`（首頁公告區塊 + 新增 Dialog） | [Spec/fn_notice/fn_notice_01_home_block.md](../Spec/fn_notice/fn_notice_01_home_block.md) |  |
| 8 | 畫面 | 調整首頁規格 `home_01.md`：新增系統公告區塊說明 | [Spec/home/home_01.md](../Spec/home/home_01.md) |  |
| 9 | Test | 建立 `_fn_notice_test_api.md` | [Spec/fn_notice/Api/_fn_notice_test_api.md](../Spec/fn_notice/Api/_fn_notice_test_api.md) |  |

## 測試案例

| ID | 類型 | 前置條件 | 操作 | 預期結果 | PG執行註記 |
|----|------|--------|------|--------| --- |
| T1 | API | 已登入（一般使用者），DB 有 2 筆有效公告（expires_at >= 今日）、1 筆已逾期 | GET /api/notices | 200，data 回傳 2 筆，依 expires_at 升冪排序，不包含逾期公告 |  |
| T2 | API | 已登入，DB 無任何有效公告 | GET /api/notices | 200，data 回傳空陣列 |  |
| T3 | API | 未登入（無 Token） | GET /api/notices | 401 未登入或 Token 過期 |  |
| T4 | API | 已登入且使用者角色具備 fn_notice 功能權限 | POST /api/notices，傳入標題「測試公告」、內容「內容文字」、有效期限為明日 | 201 新增成功，新公告立即出現於清單 |  |
| T5 | API | 已登入且使用者角色具備 fn_notice 功能權限 | POST /api/notices，標題傳入空字串 | 400 標題未填寫 |  |
| T6 | API | 已登入且使用者角色具備 fn_notice 功能權限 | POST /api/notices，內容傳入空字串 | 400 內容未填寫 |  |
| T7 | API | 已登入且使用者角色具備 fn_notice 功能權限 | POST /api/notices，有效期限傳入空值 | 400 有效期限未填寫 |  |
| T8 | API | 已登入且使用者角色具備 fn_notice 功能權限 | POST /api/notices，有效期限傳入昨日日期 | 400 有效期限須為今日或未來日期 |  |
| T9 | API | 已登入但使用者角色不具備 fn_notice 功能權限 | POST /api/notices，傳入完整合法資料 | 403 您沒有執行此操作的權限 |  |
| T10 | 畫面 | 已登入（一般使用者），DB 有有效公告 | 進入首頁 | 首頁顯示「系統公告」區塊，列出有效公告清單，每筆顯示標題與有效期限，不顯示「新增公告」按鈕 |  |
| T11 | 畫面 | 已登入（管理員，具備 fn_notice 權限），DB 有有效公告 | 進入首頁 | 首頁公告區塊顯示有效公告清單，並顯示「新增公告」按鈕 |  |
| T12 | 畫面 | 已登入，DB 無有效公告 | 進入首頁 | 公告區塊顯示「目前無公告」提示文字 |  |
| T13 | 畫面 | 已登入（管理員），在首頁公告區塊 | 點擊 [新增公告] → 填入合法標題、內容、有效期限 → 點擊 [儲存] | 表單送出成功，Dialog 關閉，公告立即出現在清單中 |  |
| T14 | 畫面 | 已登入（管理員），新增表單已開啟 | 未填任一必填欄位直接點擊 [儲存] | 顯示欄位驗證提示，禁止送出 |  |
