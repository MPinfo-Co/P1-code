# TestReport：issue-147

## TDD 規格合規

| # | 類型 | 工作內容 | 結果 |
|---|------|--------|------|
| 1 | Schema | 建立 `tb_system_params` | ✓ |
| 2 | API | 建立 `fn_setting_list_api`（查詢系統參數清單） | ✓ |
| 3 | API | 建立 `fn_setting_update_api`（更新參數值） | ✓ |
| 4 | API | 建立 `fn_setting_param_type_options_api`（取得參數類型選項） | ✓ |
| 5 | 畫面 | 建立 `fn_setting_00_overview`（功能總覽） | 跳過（前端範圍） |
| 6 | 畫面 | 建立 `fn_setting_01_list`（系統參數清單畫面） | 跳過（前端範圍） |
| 7 | 畫面 | 建立 `fn_setting_02_edit`（編輯參數值 Dialog） | 跳過（前端範圍） |
| 8 | 畫面 | 建立 `sdPrototype/fn_setting/fn_setting.html` | 跳過（前端範圍） |
| 9 | 其他 | 新增 `fn_setting` 至 `functionList.md` | 跳過（SD 範圍） |
| 10 | Test | 建立 `_fn_setting_test_api`（API 測試規格） | ✓ |

### Schema 驗證（#1）

`tb_system_params` 欄位比對結果：

| 欄位 | Schema 規格 | 實作 | 符合 |
|------|------------|------|------|
| id | INTEGER, PK | Integer, primary_key=True | ✓ |
| param_type | VARCHAR(100), NOT NULL | String(100), nullable=False | ✓ |
| param_code | VARCHAR(200), NOT NULL, UK | String(200), nullable=False, unique=True | ✓ |
| param_value | TEXT, NOT NULL | Text, nullable=False | ✓ |
| updated_by | INTEGER, NULLABLE, FK → tb_users | Integer, ForeignKey("tb_users.id"), nullable=True | ✓ |
| updated_at | TIMESTAMP, NOT NULL, DEFAULT NOW() | DateTime, nullable=False, server_default=func.now() | ✓ |

`tb_roles` 新增欄位 `can_manage_settings`：Boolean, NOT NULL, DEFAULT FALSE ✓

### API 驗證（#2、#3、#4）

**GET /api/settings**
- HTTP method & endpoint 正確 ✓
- 401 未登入或 Token 過期 ✓
- 403 您沒有執行此操作的權限 ✓
- param_type 過濾邏輯 ✓
- 依 id 升冪排序 ✓
- 回應含 param_type、param_code、param_value ✓

**PATCH /api/settings/{param_code}**
- HTTP method & endpoint 正確 ✓
- 401 未登入或 Token 過期 ✓
- 403 您沒有執行此操作的權限（無 fn_setting 權限） ✓
- 404 參數不存在 ✓
- 400 參數值不可為空 ✓
- 更新 updated_by 及 updated_at ✓
- 200 更新成功 ✓

**GET /api/settings/options/param-types**
- HTTP method & endpoint 正確 ✓
- 401 未登入或 Token 過期 ✓
- 403 您沒有執行此操作的權限 ✓（spec 要求有 fn_setting 權限才可呼叫）
- 不重複 param_type 依字母升冪排序 ✓

### Test 驗證（#10）

- pytest 數量：11（≥ 測試案例 T1–T10，共 10 筆）✓
- 每個 test function 均有 TestSpec ID 標注 ✓

## pytest 結果

通過：11 / 總計：11（tests/test_setting_api.py）

## 已知差異

- `test_migration_seed.py` 因參照的 migration 檔案（`alembic/versions/538d0579a48c_seed_initial_roles_and_admin.py`）不存在而無法收集，為既有問題，與 issue-147 無關。
- `test_ingest.py`（4 筆失敗）、`test_user_api.py`（16 筆失敗）為其他功能既有問題，與 issue-147 無關。

## 備註

- fn_setting 所有後端工作項目（Schema、三支 API、Test）驗證全數通過。
- `fn_setting_update_api` Spec 要求「管理員限制」與「fn_setting 功能權限」使用同一 `can_manage_settings` 旗標實作（兩層檢核合一），符合規格意圖。

---

## 前端 TDD 規格合規（畫面類型）

| # | 工作內容 | 結果 |
|---|---------|------|
| 5 | 建立 fn_setting_00_overview | ✓ |
| 6 | 建立 fn_setting_01_list | ✓ |
| 7 | 建立 fn_setting_02_edit | ✓ |
| 8 | 建立 sdPrototype/fn_setting/fn_setting.html | ✓ |

## 前端 TypeScript + ESLint

TypeScript: 通過（fn_setting 程式碼無型別錯誤；tsconfig.json line 17 `baseUrl` 已棄用警告為既有問題，與 issue-147 無關）
ESLint: 通過（0 警告）

## 前端備註

- 路由 `/settings/system-params` → `FnSettingList` 已在 App.jsx 正確設定。
- Sidebar「設定」群組下「系統參數」入口路徑 `/settings/system-params` 與規格一致，使用 `SettingsApplicationsOutlinedIcon`。
- API hooks（`useSettingsQuery.ts`）三支 API 路徑與 method 均與規格一致：GET `/api/settings`、GET `/api/settings/options/param-types`、PATCH `/api/settings/{paramCode}`。
- `FnSettingEdit` 以 Dialog 形式實作，參數類型／參數代碼唯讀、參數值可輸入且有不可為空驗證，符合 `fn_setting_02_edit.md` 規格。
