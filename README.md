# P1-code — MP-BOX 1.0 程式碼

MP-BOX 1.0 的前後端程式碼 repo。

## 結構

```
P1-code/
├── frontend/    # React 18 + Vite + Tailwind CSS v3
└── backend/     # FastAPI + SQLAlchemy + PostgreSQL
```

各自有獨立的 README，請依需求查看：
- [frontend/README.md](frontend/README.md)
- [backend/README.md](backend/README.md)

## 設計基準

所有 UI 以 `P1-design/Prototype/MP-Box_資安專家_v73_claude.html` 為準。

## Git 工作流程

1. 從 GitHub 開 issue → 系統自動建立對應 branch（`issue-{number}-{slug}`）
2. 在 feature branch 開發
3. 開 PR → merge 進 main

**不可直接 push 到 main。**

## Issue 命名規則

| 前綴 | 說明 |
|---|---|
| P1-x | 前端 UI 頁面 |
| P2-x | 前端基礎建設（狀態管理等） |
| P3-x | 資料庫設計（在 P1-analysis repo） |
| P4-x | 後端 API 實作 |
| P5-x | 資料庫 migration + 前後端串接 |

## 相關 Repo

| Repo | 用途 |
|---|---|
| `P1-analysis` | 需求分析、參考文件 |
| `P1-design` | 設計稿、Prototype、技術棧、Schema |
| `P1-project` | 專案管理、AI-CONTEXT.md |
