# TestReport：issue-136

## TDD 規格合規

| # | 類型 | 工作內容 | 結果 |
|---|------|--------|------|
| 1 | Schema | 建立 `tb_departments`（部門主表） | ✓ |
| 2 | Schema | 調整 `tb_users`：新增 `department_id` FK 欄位 | ✓ |
| 3 | 畫面 | 建立 `fn_dept_00_overview.md`（功能總覽） | 跳過（前端範圍） |
| 4 | 畫面 | 建立 `fn_dept_01_list.md`（部門清單畫面） | 跳過（前端範圍） |
| 5 | 畫面 | 建立 `fn_dept_02_form.md`（新增/編輯部門 Dialog） | 跳過（前端範圍） |
| 6 | 畫面 | 建立 `fn_dept_03_members.md`（部門成員列表 Dialog） | 跳過（前端範圍） |
| 7 | API | 建立 `fn_dept_query_api`（查詢部門清單，含分頁） | ✓ |
| 8 | API | 建立 `fn_dept_add_api`（新增部門） | ✓ |
| 9 | API | 建立 `fn_dept_update_api`（編輯部門） | ✓ |
| 10 | API | 建立 `fn_dept_toggle_api`（停用／啟用部門） | ✓ |
| 11 | API | 建立 `fn_dept_members_api`（查詢部門成員） | ✓ |
| 12 | API | 建立 `fn_dept_options_api`（部門下拉選項） | ✓ |
| 13 | Test | 建立 `test_dept_api.py`（pytest 測試） | ✓ |

## pytest 結果

通過：29 / 總計：29

## 已知差異

- SD spec 文件（`SD/sdSpec/fn_dept/Api/`）在本 issue 執行時尚未建立，依 TDD 測試案例直接實作。
- `_fn_dept_test_api.md` 測試規格文件未建立，測試案例以 TDD 中的測試案例清單（T1–T27）為準。
- `tb_roles` 新增 `can_manage_depts` 欄位作為 fn_dept 功能權限旗標。
- 循環 FK（`tb_departments.manager_id → tb_users`、`tb_users.department_id → tb_departments`）使用 `use_alter=True` 處理。

## 備註

- `GET /api/dept` 路由中 page 參數由程式碼手動驗證（不使用 FastAPI `ge=1`），以確保錯誤訊息為「頁碼不可小於 1」而非 middleware 攔截的 Bad Request。
- 測試檔案：`backend/tests/test_dept_api.py`，共 29 個測試案例，涵蓋 T1–T16、T22–T26 及各路由的 401/403/404 情境。

---

## 前端 TDD 規格合規（畫面類型）

| # | 工作內容 | 結果 |
|---|---------|------|
| 3 | 建立 `fn_dept_00_overview`（功能總覽規格） | ✓ 跳過（overview 無對應 TSX） |
| 4 | 建立 `fn_dept_01_list`（部門清單畫面） | ✓ `FnDeptList.tsx` |
| 5 | 建立 `fn_dept_02_form`（新增/編輯部門 Dialog） | ✓ `FnDeptForm.tsx` |
| 6 | 建立 `fn_dept_03_members`（部門成員列表 Dialog） | ✓ `FnDeptMembers.tsx` |

## 前端 TypeScript + ESLint

TypeScript: 通過（0 型別錯誤；tsconfig 中 `baseUrl` 為既有棄用警告，非本次引入）
ESLint: 通過（0 警告）

## 前端備註

- SD spec 文件（`SD/sdSpec/fn_dept/`）在本 issue 執行時尚未建立，依 TDD 測試案例（T17–T21、T27）直接實作。
- 路由 `/settings/dept` 已加入 `App.jsx`，指向 `FnDeptList`。
- Sidebar 設定群組新增「部門管理」入口（icon: AccountTreeOutlined，path: /settings/dept）。
- 分頁採 server-side pagination，透過 `useDeptQuery` 傳入 `page` / `page_size` 參數。
