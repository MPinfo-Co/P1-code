# 測試報告：issue-66 fn_user 使用者維護功能

## 基本資訊

| 項目 | 內容 |
|------|------|
| Issue | #66 |
| 功能模組 | fn_user |
| 測試檔案 | `tests/test_user_api.py` |
| 執行日期 | 2026-04-27 |
| 測試結果 | 全部通過 |

## 測試結果摘要

| 測試案例 | TestSpec ID | 測試函式 | 結果 |
|----------|-------------|----------|------|
| 查詢成功 | T1 | test_list_users_returns_200 | PASS |
| 查詢無權限 | T2 | test_list_users_no_permission_returns_403 | PASS |
| 新增成功 | T3 | test_create_user_returns_201 | PASS |
| 新增 Email 重複 | T4 | test_create_user_duplicate_email_returns_400 | PASS |
| 新增密碼不足 | T5 | test_create_user_short_password_returns_400 | PASS |
| 新增角色為空 | T6 | test_create_user_empty_roles_returns_400 | PASS |
| 修改成功 | T7 | test_update_user_returns_200 | PASS |
| 修改使用者不存在 | T8 | test_update_user_not_found_returns_404 | PASS |
| 刪除成功 | T9 | test_delete_user_returns_200 | PASS |
| 刪除自己 | T10 | test_delete_self_returns_400 | PASS |
| 未帶 Token | 額外 | test_list_users_no_token_returns_401 | PASS |

**總計：11 tests，11 passed（≥ T1–T10 共 10 個案例）**

## 執行指令

```
cd backend
pytest tests/test_user_api.py -v
```

## 備註

- `tests/conftest.py` 原有 import 路徑錯誤（`app.models.user`），已修正為 `app.db.models.user`，修正後既有 7 支測試全數通過。
- T5（密碼不足）與 T6（角色為空）由 Pydantic validator 在 422 層攔截，response body 詳細錯誤訊息中包含對應中文說明。
- `test_list_users_no_token_returns_401`：HTTPBearer 於此版本 FastAPI 回傳 401，非 403，已對應確認。
