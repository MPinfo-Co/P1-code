# CLAUDE.md

## 專案說明

MP-BOX P1-code — React 19 + FastAPI 的企業 AI 應用平台。

詳細架構與開發流程見根目錄的 `../CLAUDE.md`（P1-project）。

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
- **前端**：`ESLint` + `Prettier`（僅對暫存檔案）
- **Commit message**：commitlint 驗證格式

Commit message 格式：`{type}({scope}): 說明`
可用 type：`feat` | `fix` | `docs` | `refactor` | `test` | `chore`
