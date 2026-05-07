
# MP-box frontend
[MP-box frontend] — This is frontend of MP-box, build by React 19.2, TypeScript 6, Vite 8, backend server runs on @.env -> VITE_API_URL

## File structure
```
frontend/
├── .env                              # API base URL & env vars
├── CLAUDE.md                         # Repo guidance for Claude Code
├── dockerfile                        # Container build for the frontend
├── eslint.config.js                  # Flat ESLint config (TS + React hooks/refresh)
├── index.html                        # Vite HTML entry point
├── package-lock.json
├── package.json                      # Deps: React 19, MUI 7, Zustand, TanStack Query, Vite 8
├── tsconfig.json                     # TypeScript compiler config
├── vite.config.js                    # Vite + React plugin, /api → :8000 proxy, @ alias
│
├── public/
│   └── favicon.svg
│
└── src/
    ├── App.jsx                       # Router + route table + ProtectedRoute / PermissionGuard wiring
    ├── index.css                     # Global styles (Tailwind / resets)
    ├── main.jsx                      # Bootstraps React, MUI ThemeProvider, QueryClient
    ├── theme.js                      # MUI theme: palette, typography, DataGrid overrides
    │
    ├── components/
    │   ├── Layout/
    │   │   ├── Header.jsx            # Top bar: dynamic page title + logout button
    │   │   ├── Layout.jsx            # Sidebar + Header + <Outlet/> shell
    │   │   ├── PermissionGuard.tsx   # Blocks page render if user.functions lacks fnKey
    │   │   └── Sidebar.jsx           # Collapsible nav drawer driven by useNavigationQuery
    │   └── ui/
    │       ├── Badge.jsx             # Tailwind status pill (builtin/new/red/orange/...)
    │       ├── Modal.jsx             # Generic backdrop modal with title/footer slots
    │       └── Pagination.jsx        # Numeric pagination buttons
    │
    ├── constants/
    │   └── navigation.jsx            # ICON_MAP: function_code → MUI icon
    │
    ├── contexts/
    │   └── IssuesContext.jsx         # In-memory issues state + updateIssue() (mock data)
    │
    ├── data/                         # ── Static / mock seed data ──
    │   ├── aiPartners.ts
    │   ├── issues.js
    │   ├── knowledgeBase.ts
    │   └── users.ts
    │
    ├── pages/
    │   ├── NotFound.css / .tsx       # 404 page
    │   ├── AiPartner/                # ── fn_partner feature ──
    │   │   ├── AiPartner.css / .tsx          # Partner cards / landing
    │   │   ├── IssueDetail.css / .tsx        # Single issue view + history
    │   │   └── IssueList.css / .tsx          # Issues table for a partner
    │   ├── fn_role/                  # ── Role management ──
    │   │   ├── FnRoleForm.css / .tsx
    │   │   └── FnRoleList.css / .tsx
    │   ├── fn_user/                  # ── User management ──
    │   │   ├── FnUserForm.css / .tsx
    │   │   └── FnUserList.css / .tsx
    │   ├── Home/
    │   │   └── Home.css / .tsx               # Dashboard / landing after login
    │   ├── KnowledgeBase/            # ── KB feature (tabbed) ──
    │   │   ├── AccessTab.css / .tsx          # Permissions tab
    │   │   ├── DocTab.css / .tsx             # Documents tab
    │   │   ├── KnowledgeBase.css / .tsx      # Tab container
    │   │   └── TableTab.css / .tsx           # Tables tab
    │   ├── Login/
    │   │   └── Login.css / .tsx              # Email/password login form
    │   └── Settings/                 # ── fn_ai_config + account/role admin ──
    │       ├── Account.css / .tsx
    │       ├── AiConfig.css / .tsx
    │       └── Role.css / .tsx
    │
    ├── queries/                      # ── TanStack Query hooks (server state) ──
    │   ├── useNavigationQuery.js     # GET nav folders/items for sidebar
    │   ├── useRoleOptionsQuery.ts    # Role dropdown options
    │   ├── useRolesQuery.ts          # Roles list/CRUD
    │   ├── useUserOptionsQuery.ts    # User dropdown options
    │   └── useUsersQuery.ts          # Users list/CRUD
    │
    └── stores/
        └── authStore.ts              # Zustand: token + user, login/logout/fetchMe
```

## Rules
- Styling of componant seperate in a .css file
- Individual function store in different directory in src/pages
- When applying create or update, re-render page for new data to display

## Commands
- `npm run dev` — start dev server
- `npm run build` — production build
- `npm run lint` — run ESLint
- `npm run preview` — preview built output

## Backend server
1. Backend server runs at @.env [VITE_API_URL]