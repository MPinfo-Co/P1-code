# TestReport：[SD] Echo API

## 工作項目

**⚠️ ── AI 填寫開始，請逐行審查 ──**

| # | 類型 | 工作內容 | 參照規格 | PG執行註記 |
|---|------|--------|--------| --- |
| 1 | API | 建立 `GET /echo` 端點規格 | `Spec/framework/Api/framework_echo_api.md` | 完成：`app/api/echo.py`、`app/schemas/echo.py`，已 include 至 `main.py` |
| 2 | Test | 建立 Echo API 測試案例 | `Spec/framework/Api/_framework_test_api.md` | 完成：`tests/test_echo.py`（T1、T2） |

> Schema：無需新增或修改資料表（本端點為 stateless，不寫入任何資料）
> 畫面：無（純後端 API，無對應前端頁面）

**── AI 填寫結束 ──**

## 測試案例

**⚠️ ── AI 填寫開始，請逐行審查 ──**

| ID | 類型 | 前置條件 | 操作 | 預期結果 | PG執行註記 |
|----|------|--------|------|--------| --- |
| T1 | API | 無 | `GET /echo?message=hello` | 200，回傳 `{"message":"ok","data":"hello"}` | 通過（手動 TestClient 驗證） |
| T2 | API | 無 | `GET /echo`（不帶 `message` 參數） | 422，回傳缺少必填參數錯誤 | 通過（手動 TestClient 驗證） |

**── AI 填寫結束 ──**
