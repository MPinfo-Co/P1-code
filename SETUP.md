# 開發環境準備指引

## 前置需求

| 工具 | 最低版本 | 驗證指令 |
|------|---------|---------|
| Python | 3.11+ | `python --version` |
| Node.js | 20+ | `node --version` |
| Git | 任意 | `git --version` |

## 1. Clone 與安裝

```bash
git clone https://github.com/MPinfo-Co/P1-code.git
cd P1-code
```

## 2. Python 環境設定

```bash
cd backend
pip install -r requirements.txt
cd ..
```

## 3. 安裝 pre-commit（CLI 工具，需手動一次）

```bash
pip install pre-commit
```

> **不需要執行 `pre-commit install`**。
> Python hook 已整合進 husky，由 husky 的 `pre-commit` hook 統一呼叫。
> 只需確保 `pre-commit` 指令在 PATH 中可用即可。

## 4. 前端環境設定（hook 自動啟用）

```bash
cd frontend
npm install
```

`npm install` 會透過 `prepare` script 自動設定 husky，啟用以下本地 hook：
- **pre-commit**：對暫存的 `.js/.jsx` 檔執行 ESLint + Prettier，`.css/.json` 執行 Prettier
- **commit-msg**：commitlint 驗證 commit message 格式

## 5. Commit Message 格式

範例格式：`{type}: 工作說明`

範例：
- `feat(auth): 新增 JWT refresh token`
- `fix(api): 修正登入 500 錯誤`
- `chore(ci): 更新 GitHub Actions`

支援 Type:

| Type | 使用時機 |
|------|---------|
| `feat` | 新功能 |
| `fix` | 修復 bug |
| `docs` | 文件變更 |
| `refactor` | 重構 |
| `test` | 測試相關 |
| `chore` | 設定、建置相關 |

scope 非必填，可省略：`fix: 修正登入錯誤訊息`

## 6. 推薦 IDE 插件（VS Code）

| 插件 | 用途 |
|------|------|
| ESLint（dbaeumer.vscode-eslint） | 即時顯示 JS/JSX 錯誤 |
| Prettier（esbenp.prettier-vscode） | 儲存時自動格式化 |
| Ruff（charliermarsh.ruff） | 即時顯示 Python lint/format 錯誤 |

VS Code 建議設定（`.vscode/settings.json`）：
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

## 7. 驗證環境

### 驗證 Python hook
```bash
# 製造格式錯誤後測試
echo "x=1" >> backend/app/main.py
git add backend/app/main.py
git commit -m "chore: test"
# 預期：commit 被擋，顯示 ruff 錯誤
git checkout backend/app/main.py
```

### 驗證前端 hook
```bash
# 測試 commitlint
git commit --allow-empty -m "bad message"
# 預期：commit 被擋，顯示 type may not be empty

git commit --allow-empty -m "chore: 測試"
# 預期：通過
git reset HEAD~1
```

## 8. CI 檢查項目

每次 push 到 `issue-*` branch 或開 PR 時，CI 自動執行：

| 檢查 | 工具 |
|------|------|
| Python lint | ruff check |
| Python 格式 | ruff format --check |
| Python 測試（含 coverage） | pytest |
| 前端 lint | ESLint |
| 前端格式 | Prettier |
