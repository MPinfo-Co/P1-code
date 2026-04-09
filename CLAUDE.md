# CLAUDE.md

## 專案說明

MP-BOX P1-code — React 19 + FastAPI 的企業 AI 應用平台。

詳細架構與開發流程見根目錄的 `../CLAUDE.md`（P1-project）。

## 系統技術文件

MP-Box 的完整系統架構、資料流、SSB 整合、事件合併機制，見 [`SYSTEM.md`](./SYSTEM.md)。

## 開發環境（首次設定）

詳見 `SETUP.md`，摘要：

```bash
pip install -r backend/requirements.txt
pip install pre-commit
cd frontend && npm install
```

`npm install` 會自動啟用 git hooks（husky）。

## 本地 Hook

每次 `git commit` 自動執行：
- **Python**：`ruff check`（lint）+ `ruff format`（格式化）
- **前端**：`ESLint` + `Prettier`（僅對暫存檔案，涵蓋 `.js/.jsx/.ts/.tsx`）
- **Commit message**：commitlint 驗證格式

Commit message 格式：`{type}: 工作說明`
可用 type：`feat` | `fix` | `docs` | `refactor` | `test` | `chore`

## AI 實作指引（PG 階段）

收到 PG Issue 後，依序讀取：

| 需要什麼 | 去哪裡找 |
|----------|---------|
| 實作範圍 | PG Issue body「實作範圍」欄位 |
| API 規格 | `P1-design/Spec/` |
| 畫面規格 | `P1-design/Prototype/` |
| 本次異動 delta | `P1-design/TestPlan/issue-{SD#}-diff.md` |
| 商業邏輯背景 | `P1-analysis/issue-{SA#}/business-logic.md` |
| 測試標準 | `P1-design/TestPlan/issue-{SD#}.md` |

**前端新檔案一律使用 `.tsx`**，舊 `.jsx` 不需強制遷移（漸進式）。

**pytest 數量 ≥ TestPlan 案例數**，每個 test function 標注對應的 TestPlan ID：

```python
def test_create_leave_request(client, db_session, auth_headers):
    """對應 TestPlan issue-5 T1"""
    ...
```
