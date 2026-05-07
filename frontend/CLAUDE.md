# MP-box Frontend

React + TypeScript 前端，為 MP-box AI 工作流平台提供使用者介面。

## 技術棧

- **框架**：React 19 + TypeScript + Vite
- **UI**：MUI (Material UI) v7
- **路由**：React Router v7
- **狀態管理**：Zustand（全域 auth 狀態）
- **資料查詢**：TanStack Query v5
- **程式碼規範**：ESLint + Prettier + commitlint（Conventional Commits）

## 目錄結構

```
frontend/
├── src/
│   ├── components/           # 共用元件
│   │   ├── Layout/           # 版面配置（含 PermissionGuard）
│   │   └── ui/               # 通用 UI 元件（Badge、Modal、Pagination）
│   ├── constants/            # 靜態常數
│   ├── contexts/             # React Context（如 IssuesContext）
│   ├── data/                 # 靜態資料（aiPartners、knowledgeBase 等）
│   ├── pages/                # 路由頁面
│   │   ├── AiPartner/        # AI 夥伴列表與詳情
│   │   ├── Home/
│   │   ├── KnowledgeBase/
│   │   ├── Login/
│   │   ├── Settings/
│   │   ├── fn_role/          # 角色管理
│   │   └── fn_user/          # 使用者管理
│   ├── queries/              # TanStack Query hooks（API 呼叫）
│   ├── stores/               # Zustand stores（authStore）
│   ├── App.jsx               # 路由設定
│   ├── main.jsx              # 應用程式進入點
│   └── theme.js              # MUI 主題設定
├── .claude/
│   └── agents/               # Claude Code subagent 定義
├── CLAUDE.md
├── package.json
├── tsconfig.json
└── vite.config.js
```

## 常用指令

```bash
npm run dev       # 啟動開發伺服器（port 5173）
npm run build     # 生產環境建置
npm run lint      # ESLint 檢查
npm run preview   # 預覽生產建置
```

## 開發慣例

### 檔案命名
- 頁面元件：`PascalCase.tsx`（例：`IssueDetail.tsx`）
- Query hooks：`use<Resource>Query.ts`（例：`useUsersQuery.ts`）
- Stores：`<name>Store.ts`（例：`authStore.ts`）
- 路徑別名：`@/` 對應 `src/`（例：`import useAuthStore from '@/stores/authStore'`）

### 元件撰寫
- 所有新元件使用 `.tsx` 副檔名
- Props 以 TypeScript interface 定義，命名為 `<ComponentName>Props`
- 使用 MUI 元件（`@mui/material`、`@mui/icons-material`），勿自行實作基礎 UI
- MUI 元件使用具名 import（`import Box from '@mui/material/Box'`），避免 barrel import

### 狀態與資料存取
- 全域 auth 狀態：`useAuthStore`（Zustand）
- API 呼叫：在 `src/queries/` 建立 TanStack Query hook
- API base URL：`import.meta.env.VITE_API_URL`
- 認證 token：`useAuthStore.getState().token`，加入 `Authorization: Bearer <token>` header

### 權限控制
- 路由層級使用 `PermissionGuard`（`src/components/Layout/PermissionGuard.tsx`）

## 與後端溝通

- 後端服務：`http://localhost:8000`（開發時透過 Vite proxy `/api` 轉發）
- 認證：JWT Bearer token（登入後由 `authStore` 保存）
- 資料格式：JSON，回應結構通常為 `{ data: [...] }` 或直接回傳陣列

## .claude 目錄

```
.claude/
└── agents/
    └── react_agent.md    # React subagent — 元件撰寫與 MUI 整合
```
