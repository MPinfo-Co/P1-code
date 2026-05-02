# TestReport：[SD] 移除測試用功能：公告功能（fn_notice）及系統參數設定功能（fn_setting）

## 工作項目

**⚠️ ── AI 填寫開始，請逐行審查 ──**

| # | 類型 | 工作內容 | 參照規格 | PG執行註記 |
|---|------|--------|--------| --- |
| 1 | Schema | 刪除 `fn_setting` 區塊：移除 `tb_system_params` 資料表定義 | SD/schema.md |  |
| 2 | 畫面 | 刪除 `fn_setting` 畫面規格目錄：移除 `SD/sdSpec/fn_setting/` 整個目錄（含 `fn_setting_00_overview.md`、`fn_setting_01_list.md`、`fn_setting_02_edit.md`） | SD/sdSpec/fn_setting/ |  |
| 3 | 其他 | 刪除 `fn_setting` API 規格：移除 `SD/sdSpec/fn_setting/Api/` 下所有 API 規格（`fn_setting_list_api.md`、`fn_setting_update_api.md`、`fn_setting_param_type_options_api.md`、`_fn_setting_test_api.md`） | SD/sdSpec/fn_setting/Api/ |  |
| 4 | 畫面 | 刪除 `fn_setting` 原型畫面：移除 `SD/sdPrototype/fn_setting/` 整個目錄（含 `fn_setting.html`、`_data.js`） | SD/sdPrototype/fn_setting/ |  |
| 5 | 其他 | 從 `functionList.md` 移除 `fn_setting` 功能項目 | SD/functionList.md |  |
| 6 | 其他 | 確認 `fn_notice` 在 SD 設計文件中無對應規格（無 sdSpec、無 sdPrototype、無 schema 定義），SD 無需異動；fn_notice 相關程式碼移除為 PG 工作範疇 | — |  |

**── AI 填寫結束 ──**

## 測試案例

**⚠️ ── AI 填寫開始，請逐行審查 ──**

| ID | 類型 | 前置條件 | 操作 | 預期結果 | PG執行註記 |
|----|------|--------|------|--------| --- |
| T1 | Schema | `SD/schema.md` 含 `fn_setting` 區塊（`tb_system_params`） | 移除 `fn_setting` 區塊 | `SD/schema.md` 中不再出現 `tb_system_params` 及其欄位定義 |  |
| T2 | 畫面 | `SD/sdSpec/fn_setting/` 目錄存在 | 刪除 `SD/sdSpec/fn_setting/` 整個目錄 | 目錄及所有子檔案不存在 |  |
| T3 | 其他 | `SD/sdSpec/fn_setting/Api/` 目錄存在，含三支 API 規格與 test 檔 | 刪除 `SD/sdSpec/fn_setting/Api/` 整個目錄 | 目錄及所有子檔案不存在 |  |
| T4 | 畫面 | `SD/sdPrototype/fn_setting/` 目錄存在 | 刪除 `SD/sdPrototype/fn_setting/` 整個目錄 | 目錄及所有子檔案不存在 |  |
| T5 | 其他 | `SD/functionList.md` 含 `fn_setting` 功能列 | 移除 `fn_setting` 列 | `SD/functionList.md` 中不再出現 `fn_setting` |  |
| T6 | 其他 | 確認 `fn_notice` 在 SD 文件範疇無設計產出（schema.md 無 `tb_notices`、無 `can_manage_notices`；sdSpec/ 無 fn_notice 目錄；sdPrototype/ 無 fn_notice 目錄） | 搜尋確認 | SD 設計文件中找不到任何 fn_notice 相關項目，確認 SD 無需進行額外異動 |  |

**── AI 填寫結束 ──**

## 設計決定

**⚠️ ── AI 填寫開始，請逐行審查 ──**

1. **fn_notice 在 SD 範疇無工作項目**：fn_notice 的程式碼實作（後端 API、Model、前端元件）均在 P1-code Repo，SD 設計文件（sdSpec、sdPrototype、schema.md）從未為 fn_notice 建立對應規格，故本次 SD 工作項目僅含刪除 fn_setting 相關設計文件。fn_notice 程式碼移除為 PG Issue 工作範疇。

2. **直接刪除 fn_setting 全部設計文件**：fn_setting 功能不在正式產品規劃內，且為純刪除需求，無需保留任何版本記錄。依「活文件原則」，設計文件永遠反映最新狀態，直接刪除目錄即可。

**── AI 填寫結束 ──**
