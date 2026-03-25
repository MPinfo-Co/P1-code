# Frontend — MP-BOX 1.0

React 18 + Vite 前端應用程式。

## 技術棧

| 套件 | 版本 | 用途 |
|---|---|---|
| React | 18 | UI 框架 |
| Vite | 6 | 開發伺服器 + 打包工具 |
| Tailwind CSS | v3 | 樣式 |
| shadcn/ui | base-nova | UI 元件庫 |
| React Router | v6 | 前端路由 |
| lucide-react | — | Icon |

## 環境建置

```bash
cd frontend
npm install
npm run dev
```

開啟 `http://localhost:5173`

## 專案結構

```
src/
├── App.jsx                  # 路由設定、Provider 包裝
├── main.jsx                 # 入口
├── index.css                # 全域樣式（Tailwind）
├── components/
│   ├── Layout/
│   │   ├── Layout.jsx       # 整體框架（Sidebar + Header + 主內容區）
│   │   ├── Sidebar.jsx      # 左側導覽列
│   │   └── Header.jsx       # 頂部列
│   └── ui/                  # shadcn/ui 元件（button、badge、modal 等）
├── contexts/
│   ├── AuthContext.jsx      # 登入狀態管理（user、login()、logout()）
│   └── IssuesContext.jsx    # 安全事件狀態
├── data/                    # Mock 資料（串接 API 前使用）
│   ├── users.js             # 使用者 + 角色
│   ├── issues.js            # 安全事件
│   ├── aiPartners.js        # AI 夥伴
│   └── knowledgeBase.js     # 知識庫
├── lib/
│   └── utils.js             # shadcn/ui 工具函式
└── pages/
    ├── Login/
    │   └── Login.jsx        # 登入頁
    ├── Home/
    │   └── Home.jsx         # 首頁 Dashboard
    ├── AiPartner/
    │   ├── AiPartner.jsx    # AI 夥伴選擇頁
    │   ├── IssueList.jsx    # 安全事件清單
    │   └── IssueDetail.jsx  # 安全事件詳情
    ├── KnowledgeBase/
    │   ├── KnowledgeBase.jsx
    │   ├── DocTab.jsx
    │   ├── TableTab.jsx
    │   └── AccessTab.jsx
    ├── Settings/
    │   ├── Account.jsx      # 帳號管理
    │   ├── Role.jsx         # 角色管理
    │   └── AiConfig.jsx     # AI 夥伴設定
    └── NotFound.jsx
```

## 路由結構

```
/login              → Login.jsx（未登入才能進）
/                   → Home.jsx（需登入）
/ai-partner         → AiPartner.jsx
/ai-partner/:id/issues        → IssueList.jsx
/ai-partner/:id/issues/:id    → IssueDetail.jsx
/kb                 → KnowledgeBase.jsx
/settings/account   → Account.jsx
/settings/role      → Role.jsx
/settings/ai-config → AiConfig.jsx
```

未登入訪問受保護路由 → 自動導向 `/login`

## 登入機制（目前為 Mock）

`AuthContext.jsx` 管理登入狀態，存於 `localStorage`。

**目前狀態：** mock 驗證，對照 `src/data/users.js`，密碼固定 `123`

**預期改動（P5-2）：**
- `Login.jsx`：改為 `POST /api/auth/login`
- `AuthContext.jsx`：改為存 JWT token，API 請求帶 Authorization header

## Mock 測試帳號

| 帳號 | 密碼 | 角色 |
|---|---|---|
| rex | 123 | 管理員 |
| robert | 123 | 一般使用者 |

## 新增頁面流程

1. 在 `src/pages/` 建立對應資料夾與 `.jsx` 檔案
2. 在 `App.jsx` 加入 `<Route>`
3. 在 `Sidebar.jsx` 加入導覽項目（如需要）
4. UI 以 `v73_claude.html` 設計稿為準

## 待串接（未完成）

| 功能 | 現況 | 預計 issue |
|---|---|---|
| 登入驗證 | Mock | P5-2 |
| 安全事件資料 | Mock JSON | P5-2 |
| AI 夥伴資料 | Mock JSON | P5-2 |
| 知識庫資料 | Mock JSON | P5-2 |
