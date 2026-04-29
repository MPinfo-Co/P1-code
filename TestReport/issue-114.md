# TestReport：[SD] Prototype 介面風格優化

## 工作項目
| # | 類型 | 工作內容 | 參照規格 | PG執行註記 |
|---|------|--------|--------| --- |
| 1 | 畫面 | 調整 `frontend/src/pages/fn_user/FnUserList.tsx`：移除頁面標題 Box（含 `<Typography variant="h6">使用者管理</Typography>` 與「新增使用者」Button 的外層 Box） | `Prototype/fn_user.html` |  |
| 2 | 畫面 | 調整 `frontend/src/pages/fn_user/FnUserList.tsx`：「新增使用者」`<Button>` 移至 filter bar Box 最後一個子元素，加 `sx={{ ml: 'auto' }}` 使其靠右 | `Prototype/fn_user.html` |  |
| 3 | 畫面 | 調整 `frontend/src/pages/fn_user/FnUserList.tsx`：filter bar Box sx 改為 `bgcolor: '#f1f5f9'`、`borderRadius: '4px'`、`padding: '5px 12px'`、`flexWrap: 'nowrap'`、`mb: '5px'` | `Prototype/_style.css` |  |
| 4 | 畫面 | 調整 `frontend/src/pages/fn_user/FnUserList.tsx`：filter bar 內篩選標籤（`InputLabel`、`TextField` label）加 `sx={{ color: '#1e293b', fontWeight: 700 }}`（或 `InputLabelProps`） | `Prototype/_style.css` |  |
| 5 | 畫面 | 調整 `frontend/src/pages/fn_user/FnUserList.tsx`：filter bar 內「套用」Button 加 `sx={{ borderRadius: '3px' }}`；table card Box `borderRadius` 改為 `'4px'` | `Prototype/_style.css` |  |
| 6 | 畫面 | 調整 `frontend/src/pages/fn_user/FnUserList.tsx`：DataGrid sx 補充 `'& .MuiDataGrid-columnHeaders': { bgcolor: '#f1f5f9' }`、`'& .MuiDataGrid-cell': { py: '6px' }`；名稱欄 renderCell `fontWeight` `600` → `400` | `Prototype/_style.css` |  |

## 測試案例
| ID | 類型 | 前置條件 | 操作 | 預期結果 | PG執行註記 |
|----|------|--------|------|--------| --- |
| T1 | 畫面 | 開啟使用者管理頁（已登入） | 檢視主內容區頂端 | 無獨立頁面標題列，主內容區直接由 filter bar 開始 |  |
| T2 | 畫面 | 開啟使用者管理頁（已登入） | 檢視 filter bar | 「新增使用者」按鈕位於 filter bar 最右側，與「套用」並排同列 |  |
| T3 | 畫面 | 開啟使用者管理頁（已登入） | 檢視 filter bar 背景色與高度 | Filter bar 背景色為 `#f1f5f9`，視覺高度與表格標題列（column headers）相近 |  |
| T4 | 畫面 | 開啟使用者管理頁（已登入） | 檢視 filter bar 篩選標籤文字 | 「角色職位」與「關鍵字搜尋」標籤顏色深色（`#1e293b`）且加粗 |  |
| T5 | 畫面 | 開啟使用者管理頁（已登入） | 檢視「套用」按鈕與 table card 圓角 | 按鈕圓角為 3px，table card 圓角為 4px |  |
| T6 | 畫面 | 開啟使用者管理頁（已登入） | 檢視表格標題列與名稱欄 | Column headers 背景色為 `#f1f5f9`；名稱文字 font-weight 為 400（非粗體） |  |

**⚠️ ── AI 填寫開始，請逐行審查 ──**

### 設計決定說明

**工作項目 1（移除頁面標題 Box）**：頁面標題由 Header layout 統一顯示（規格：Header 左側為最大最深字）。Header layout 元件尚未實作，為獨立工作；本 TDD 的對應處理為移除主內容區的重複標題，待 Header 建立後即完整符合規格。

**工作項目 4（filter-label 深色粗體）**：MUI 使用浮動 `InputLabel` 而非 prototype 的外部 `<label>`，兩者位置不同。本工作項目要求的是視覺效果一致（深色、加粗），實作方式由 PG 決定（可改用外部 label 或沿用 MUI InputLabelProps）。

**工作項目 5（按鈕圓角）**：只調整 filter bar 內的「套用」Button；FnUserForm 內的按鈕（儲存、取消）為 Dialog 操作按鈕，風格獨立，不在本次範圍。

**範圍說明**：本 TDD 涵蓋 P1-code 中已實作的 fn_user 頁面（`FnUserList.tsx`）。其他頁面（fn_role、events、kb 等）尚未有 .tsx 實作，待各頁面對應 Issue 依此規格建立。Header / Sidebar layout 元件亦為獨立 Issue，不含於本次工作項目。

**Prototype 同步說明**：`Prototype/` HTML 雛形已於 sa-108 分支（PR #109）完成視覺調整並 merge。本 TDD 的參照規格（`Prototype/fn_user.html`、`Prototype/_style.css`）即為最新狀態，無需再次修改。

**── AI 填寫結束 ──**
