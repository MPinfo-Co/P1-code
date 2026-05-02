# TestReport：issue-155

## TDD 規格合規

| # | 類型 | 工作內容 | 結果 |
|---|------|--------|------|
| T1 | Schema | fn_setting backend 程式碼移除（router、schema、model、test 刪除；main.py import/include_router 移除） | ✓ |
| T2 | Schema | fn_notice backend 程式碼移除（router、schema、model、test 刪除；main.py import/include_router 移除） | ✓ |
| T3 | Schema | drop table migration 建立（b2c3d4e5f6a7_drop_fn_notice_fn_setting_tables.py） | ✓ |

## 異動清單

### 刪除檔案
- `backend/app/api/notice.py`
- `backend/app/api/setting.py`
- `backend/app/api/schema/notice.py`
- `backend/app/api/schema/setting.py`
- `backend/app/db/models/fn_notice.py`
- `backend/app/db/models/fn_setting.py`
- `backend/tests/test_notice_api.py`
- `backend/tests/test_setting_api.py`

### 修改檔案
- `backend/app/main.py`：移除 notice_router、setting_router 的 import 及 include_router
- `backend/app/db/models/__init__.py`：移除 Notice、SystemParam import
- `backend/app/db/models/fn_user_role.py`：移除 Role.can_manage_notices、Role.can_manage_settings 欄位
- `backend/tests/conftest.py`：移除 Notice、SystemParam 的 import 及 _SEED_TABLES 條目

### 新增檔案
- `backend/bpBoxAlembic/versions/b2c3d4e5f6a7_drop_fn_notice_fn_setting_tables.py`：drop tb_notices、tb_system_params 及 tb_roles 的 can_manage_notices、can_manage_settings 欄位

## pytest 結果

通過：24 / 總計：28（含 4 個預存在失敗，與本 issue 無關）

## 備註

- `tests/test_migration_seed.py`（集合錯誤）及 `tests/test_ingest.py`（4 個失敗）在本 issue 實作前即已存在，與 fn_notice/fn_setting 移除無關，屬既有問題。
- 移除 fn_setting 後，Role model 中的 can_manage_notices 及 can_manage_settings 欄位一併從 ORM 移除，migration 中同步以 drop_column 處理。
