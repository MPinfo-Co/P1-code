# TestReport：[SD] 新增部門資料維護功能

## 工作項目

**⚠️ ── AI 填寫開始，請逐行審查 ──**

| # | 類型 | 工作內容 | 參照規格 | PG執行註記 |
|---|------|--------|--------| --- |
| 1 | Schema | 建立 `tb_departments`（部門主表） | `SD/schema.md` |  |
| 2 | Schema | 調整 `tb_users`：新增 `department_id` FK 欄位 | `SD/schema.md` |  |
| 3 | 畫面 | 建立 `fn_dept_00_overview.md`（功能總覽） | `SD/sdSpec/fn_dept/fn_dept_00_overview.md` |  |
| 4 | 畫面 | 建立 `fn_dept_01_list.md`（部門清單畫面） | `SD/sdSpec/fn_dept/fn_dept_01_list.md` |  |
| 5 | 畫面 | 建立 `fn_dept_02_form.md`（新增/編輯部門 Dialog） | `SD/sdSpec/fn_dept/fn_dept_02_form.md` |  |
| 6 | 畫面 | 建立 `fn_dept_03_members.md`（部門成員列表 Dialog） | `SD/sdSpec/fn_dept/fn_dept_03_members.md` |  |
| 7 | API | 建立 `fn_dept_query_api`（查詢部門清單，含分頁：每頁筆數、頁碼） | `SD/sdSpec/fn_dept/Api/fn_dept_query_api.md` |  |
| 8 | API | 建立 `fn_dept_add_api`（新增部門） | `SD/sdSpec/fn_dept/Api/fn_dept_add_api.md` |  |
| 9 | API | 建立 `fn_dept_update_api`（編輯部門） | `SD/sdSpec/fn_dept/Api/fn_dept_update_api.md` |  |
| 10 | API | 建立 `fn_dept_toggle_api`（停用／啟用部門） | `SD/sdSpec/fn_dept/Api/fn_dept_toggle_api.md` |  |
| 11 | API | 建立 `fn_dept_members_api`（查詢部門成員） | `SD/sdSpec/fn_dept/Api/fn_dept_members_api.md` |  |
| 12 | API | 建立 `fn_dept_options_api`（部門下拉選項，供表單使用） | `SD/sdSpec/fn_dept/Api/fn_dept_options_api.md` |  |
| 13 | Test | 建立 `_fn_dept_test_api.md`（fn_dept API 測試規格） | `SD/sdSpec/fn_dept/Api/_fn_dept_test_api.md` |  |

## 測試案例

| ID | 類型 | 前置條件 | 操作 | 預期結果 | PG執行註記 |
|----|------|--------|------|--------| --- |
| T1 | API | 已登入且具備 fn_dept 功能權限，DB 有多筆部門 | GET /api/dept | 200，data.items 包含當頁部門，data.total / page / page_size 正確 |  |
| T2 | API | 已登入且具備 fn_dept 功能權限，DB 有名稱含「業務」的部門 | GET /api/dept?keyword=業務 | 200，data.items 只包含名稱或代碼含「業務」的部門 |  |
| T3 | API | 已登入但不具備 fn_dept 功能權限 | GET /api/dept | 403 您沒有執行此操作的權限 |  |
| T4 | API | 已登入且具備 fn_dept 功能權限，部門代碼「IT001」不存在 | POST /api/dept，傳入有效名稱、代碼「IT001」 | 201 新增成功 |  |
| T5 | API | 已登入且具備 fn_dept 功能權限，部門代碼「IT001」已存在 | POST /api/dept，傳入代碼「IT001」 | 400 此部門代碼已被使用 |  |
| T6 | API | 已登入且具備 fn_dept 功能權限，上級部門已在第 3 層 | POST /api/dept，傳入上級部門 id 為第 3 層部門 | 400 部門層級最多 3 層，無法在此部門下新增子部門 |  |
| T7 | API | 已登入且具備 fn_dept 功能權限，目標部門存在 | PATCH /api/dept/{id}，傳入新名稱 | 200 更新成功 |  |
| T8 | API | 已登入且具備 fn_dept 功能權限 | PATCH /api/dept/99999 | 404 部門不存在 |  |
| T9 | API | 已登入且具備 fn_dept 功能權限，部門代碼「B001」已被另一部門使用 | PATCH /api/dept/{id}，代碼傳入「B001」 | 400 此部門代碼已被使用 |  |
| T10 | API | 已登入且具備 fn_dept 功能權限，目標部門存在且無成員 | PATCH /api/dept/{id}/toggle（is_active=false） | 200 停用成功 |  |
| T11 | API | 已登入且具備 fn_dept 功能權限，目標部門存在且有成員 | PATCH /api/dept/{id}/toggle（is_active=false） | 400 此部門仍有人員，無法停用 |  |
| T12 | API | 已登入且具備 fn_dept 功能權限，已停用部門存在 | PATCH /api/dept/{id}/toggle（is_active=true） | 200 啟用成功 |  |
| T13 | API | 已登入且具備 fn_dept 功能權限，目標部門存在且有成員 | GET /api/dept/{id}/members | 200，data 包含成員 id 及姓名列表 |  |
| T14 | API | 已登入且具備 fn_dept 功能權限，目標部門無成員 | GET /api/dept/{id}/members | 200，data 為空陣列 |  |
| T22 | API | 已登入但不具備 fn_dept 功能權限 | GET /api/dept/{id}/members | 403 您沒有執行此操作的權限 |  |
| T23 | API | 已登入且具備 fn_dept 功能權限 | GET /api/dept/99999/members | 404 部門不存在 |  |
| T24 | API | 已登入且具備 fn_dept 功能權限，DB 有 30 筆部門 | GET /api/dept?page=2&page_size=10 | 200，data.items 含第 11–20 筆，total=30，page=2，page_size=10 |  |
| T25 | API | 已登入且具備 fn_dept 功能權限 | GET /api/dept?page_size=7 | 400 每頁筆數僅允許 10、25 或 50 |  |
| T26 | API | 已登入且具備 fn_dept 功能權限 | GET /api/dept?page=0 | 400 頁碼不可小於 1 |  |
| T15 | API | 已登入 | GET /api/dept/options | 200，data 為啟用中且層級未達第 3 層的部門 `[{ id, name }]` |  |
| T16 | API | 未登入 | GET /api/dept/options | 401 未登入或 Token 過期 |  |
| T17 | 畫面 | 已登入且具備 fn_dept 功能權限，DB 有多筆部門 | 進入部門管理清單畫面 | 顯示部門表格（名稱、代碼、上級部門、負責人、狀態、操作欄） |  |
| T18 | 畫面 | 清單畫面已載入 | 點擊「新增部門」 | 開啟新增部門 Dialog，欄位皆為空白 |  |
| T19 | 畫面 | 清單畫面已載入 | 點擊某列「編輯」 | 開啟編輯部門 Dialog，帶入現有資料 |  |
| T20 | 畫面 | 目標部門無成員 | 點擊「停用」 → 確認停用 | 清單重新整理，該部門狀態變為停用 |  |
| T21 | 畫面 | 清單畫面已載入，DB 有超過 10 筆部門 | 切換分頁至第 2 頁 | 清單顯示第 11 筆起的部門，分頁資訊更新 |  |
| T27 | 畫面 | 清單畫面已載入 | 點擊「查看人員」 | 開啟成員列表 Dialog，顯示成員姓名 |  |

**── AI 填寫結束 ──**
