# P1-code — 系統開發（PG／AI）

> [← 回到 P1 總導覽](https://github.com/MPinfo-Co/P1-project#readme)

P1 產品的前後端程式碼庫。React 19（JavaScript）+ FastAPI，由 PG 或 AI 依據 SD 規格實作。

## 在四 Repo 流程中的角色

```
P1-project（PM）→ P1-analysis（SA）→ P1-design（SD）
    └─ D-workflow 自動建立 PG Issue + C-Branch + Draft PR
        └─ P1-code（PG／AI）  ← 你在這裡
            └─ PG merge → PG Issue 自動關閉，VersionDiff 自動產生
```

## 目錄結構

```
P1-code/
├── frontend/                     # React 19 + Vite + JavaScript + MUI
├── backend/                      # Python FastAPI + SQLAlchemy + PostgreSQL
├── PG測試報告/
│   └── issue-{N}.md              # 測試報告（系統建立框架，PG 填寫結果）
└── VersionDiff/
    └── issue-{N}_{author}_{date}.md  # merge 時自動產生，記錄程式碼異動
```

詳細說明：[frontend/README.md](frontend/README.md)・[backend/README.md](backend/README.md)

## PG／AI 工作起點

收到 PG Issue 後，沿關聯鏈讀取資訊：

| 需要什麼 | 去哪裡找 |
|----------|---------|
| 實作範圍 | PG Issue body「實作範圍」欄位 |
| API 規格 | `P1-design/Spec/` |
| 畫面規格 | `P1-design/Prototype/` |
| 本次異動 delta | `P1-design/TestPlan/issue-{SD#}-diff.md` |
| 商業邏輯背景 | `P1-analysis/issue-{SA#}/business-logic.md` |
| 測試標準 | `P1-design/TestPlan/issue-{SD#}.md` |

1. Pull 分支（Issue body 中有分支連結）
2. 依 Spec 實作前後端程式碼
3. 依 TestPlan 撰寫 pytest 測試（數量 ≥ TestPlan 案例數）
4. Push → CI 自動執行（Ruff + Pytest + ESLint）
5. CI 通過後把 Draft PR 轉 **Ready for Review**，指派 2 位審查人
6. Merge 後 PG Issue 自動關閉，VersionDiff 自動產生

**Branch 命名：** `issue-{N}-{slug}`（由系統建立，不可直接 push main）

## 完整工作流程規範

請參考 [P1-project/docs/workflow/quick-start.md](https://github.com/MPinfo-Co/P1-project/blob/main/docs/workflow/quick-start.md)

## 環境設定

新成員首次設定請見 [SETUP.md](SETUP.md)
