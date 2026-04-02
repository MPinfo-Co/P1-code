# P5-2 前端串接 JWT API 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 將前端登入從 mock 驗證改為呼叫真實後端 JWT API（`POST /api/auth/login`）。

**Architecture:** 以 `VITE_API_URL` 環境變數管理 API 位址，authStore 改為 async 並存取 JWT token，Login.jsx 改為 email 輸入並呼叫 store。ProtectedRoute 改判斷 token。

**Tech Stack:** React 19, Vite, Zustand, fetch API

---

## 前置確認

- branch：`issue-23-p5-2-mock-data-api`
- 後端已啟動：`sudo service postgresql start` → `source venv/bin/activate` → `uvicorn app.main:app --reload`
- 測試帳號：`admin@mpinfo.com.tw` / `@Admin1234`（由 seed.py 建立）

---

## 檔案異動總覽

| 動作 | 檔案 |
|---|---|
| 新增 | `frontend/.env.local` |
| 新增 | `frontend/.env.example` |
| 修改 | `frontend/src/stores/authStore.js` |
| 修改 | `frontend/src/pages/Login/Login.jsx` |
| 修改 | `frontend/src/App.jsx` |

---

## Task 1：建立環境變數檔案

**Files:**
- Create: `frontend/.env.local`
- Create: `frontend/.env.example`

- [ ] **Step 1：建立 `.env.local`（本地開發用，不進 git）**

  在 `frontend/` 目錄下建立 `.env.local`，內容：
  ```
  VITE_API_URL=http://localhost:8000
  ```

- [ ] **Step 2：建立 `.env.example`（進 git，讓其他人知道要設什麼）**

  在 `frontend/` 目錄下建立 `.env.example`，內容：
  ```
  # 本地開發預設值，staging/production 在 Vercel Dashboard 設定
  VITE_API_URL=http://localhost:8000
  ```

- [ ] **Step 3：確認 `.gitignore` 已涵蓋 `.env.local`**

  `frontend/.gitignore` 第 13 行有 `*.local`，已涵蓋，無需修改。

- [ ] **Step 4：commit**

  ```bash
  cd frontend
  git add .env.example
  git commit -m "feat: add VITE_API_URL env config for JWT API"
  ```
  （`.env.local` 被 gitignore 排除，不加入 commit）

---

## Task 2：更新 authStore.js

**Files:**
- Modify: `frontend/src/stores/authStore.js`

目前 store 只存 `user`（username + role），改為存 `token` + `user`，login/logout 改為 async。

> **注意**：`Header.jsx` 的登出 `onClick` 不需要加 `await`——logout 內部已用 `.catch()` 處理後端錯誤，最終一定會清除 token，跳頁行為不受影響。

- [ ] **Step 1：更新 `authStore.js`**

  將檔案內容替換為：

  ```js
  // src/stores/authStore.js
  import { create } from 'zustand'

  const BASE_URL = import.meta.env.VITE_API_URL

  const useAuthStore = create((set, get) => ({
    token: localStorage.getItem('mp-box-token') || null,
    user: null, // 刷新後為 null，待 GET /api/users/me 實作後補齊

    login: async (email, password) => {
      const res = await fetch(`${BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (res.status === 401) throw new Error('帳號或密碼錯誤')
      if (!res.ok) throw new Error('伺服器錯誤，請稍後再試')
      const { access_token } = await res.json()
      localStorage.setItem('mp-box-token', access_token)
      set({ token: access_token, user: { email } })
    },

    logout: async () => {
      await fetch(`${BASE_URL}/api/auth/logout`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${get().token}` },
      }).catch((err) => { console.warn('[logout] backend call failed:', err) })
      localStorage.removeItem('mp-box-token')
      localStorage.removeItem('mp-box-user') // 清除舊版 mock key
      set({ token: null, user: null })
    },
  }))

  export function useAuth() {
    return useAuthStore()
  }

  export default useAuthStore
  ```

- [ ] **Step 2：commit**

  ```bash
  git add frontend/src/stores/authStore.js
  git commit -m "feat: authStore async login/logout with JWT token"
  ```

---

## Task 3：更新 Login.jsx

**Files:**
- Modify: `frontend/src/pages/Login/Login.jsx`

移除 mock 邏輯，改為 async 呼叫 authStore.login()，input 改為 email。

- [ ] **Step 1：更新 `Login.jsx`**

  將檔案內容替換為：

  ```jsx
  import { useState } from 'react'
  import { useNavigate } from 'react-router-dom'
  import { useAuth } from '../../stores/authStore'

  export default function Login() {
    const { login } = useAuth()
    const navigate = useNavigate()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)

    async function handleSubmit(e) {
      e.preventDefault()
      setError('')
      setLoading(true)
      try {
        await login(email, password)
        navigate('/')
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-[#1e2d52] to-[#2e3f6e]">
        <div className="bg-white rounded-xl shadow-2xl p-12 w-full max-w-[430px] text-center">
          <h1 className="text-4xl font-black text-slate-800 mb-8">MP-Box</h1>
          <form onSubmit={handleSubmit} className="space-y-5 text-left">
            <div>
              <label className="block text-sm font-semibold text-slate-600 mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg bg-slate-50 focus:border-indigo-500 outline-none"
                placeholder="輸入 Email"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-600 mb-2">密碼</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg bg-slate-50 focus:border-indigo-500 outline-none"
                placeholder="密碼"
                required
              />
            </div>
            {error && <p className="text-red-500 text-sm font-medium">{error}</p>}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 bg-[#2e3f6e] text-white rounded-lg text-base font-bold hover:bg-[#1e2d52] transition-colors disabled:opacity-60"
            >
              {loading ? '登入中...' : '登入系統'}
            </button>
          </form>
        </div>
      </div>
    )
  }
  ```

- [ ] **Step 2：commit**

  ```bash
  git add frontend/src/pages/Login/Login.jsx
  git commit -m "feat: Login.jsx calls real JWT API, email input"
  ```

---

## Task 4：更新 App.jsx（ProtectedRoute）

**Files:**
- Modify: `frontend/src/App.jsx`

ProtectedRoute 目前判斷 `user !== null`，改為判斷 `token !== null`。

- [ ] **Step 1：修改 `App.jsx` 中的 ProtectedRoute 與 AppRoutes**

  找到這兩段並替換：

  **找到 `function ProtectedRoute`：**
  ```jsx
  // 修改前
  function ProtectedRoute({ children }) {
    const { user } = useAuth()
    return user ? children : <Navigate to="/login" replace />
  }

  // 修改後
  function ProtectedRoute({ children }) {
    const { token } = useAuth()
    return token ? children : <Navigate to="/login" replace />
  }
  ```

  **找到 `function AppRoutes` 裡的登入判斷：**
  ```jsx
  // 修改前
  const { user } = useAuth()
  element={user ? <Navigate to="/" replace /> : <Login />}

  // 修改後
  const { token } = useAuth()
  element={token ? <Navigate to="/" replace /> : <Login />}
  ```

- [ ] **Step 2：commit**

  ```bash
  git add frontend/src/App.jsx
  git commit -m "feat: ProtectedRoute checks token instead of user"
  ```

---

## Task 5：手動測試

確保後端已啟動（`uvicorn app.main:app --reload`）再進行測試。

- [ ] **Step 1：啟動前端**

  ```bash
  cd frontend
  npm run dev
  ```

- [ ] **Step 2：測試登入成功**

  1. 打開 `http://localhost:5173`
  2. 未登入應自動跳至 `/login`
  3. 輸入 `admin@mpinfo.com.tw` / `@Admin1234`，點「登入系統」
  4. 應進入首頁（`/`）
  5. 打開 DevTools > Application > Local Storage，確認有 `mp-box-token` key

- [ ] **Step 3：測試頁面重整保持登入**

  1. 登入後按 F5 重整
  2. 應維持登入狀態，不跳回 `/login`

- [ ] **Step 4：測試登出**

  1. 點 Header 右上角登出
  2. 應跳回 `/login`
  3. Local Storage 的 `mp-box-token` 應消失
  4. 舊版 `mp-box-user` key 也應消失（若存在）

- [ ] **Step 5：測試登入失敗**

  1. 輸入錯誤密碼，點「登入系統」
  2. 應顯示「帳號或密碼錯誤」
  3. 不應跳頁

- [ ] **Step 6：測試 CORS（若出現錯誤）**

  若瀏覽器 console 出現 CORS error，後端需在 `main.py` 確認 `origins` 已包含 `http://localhost:5173`。

---

## Task 6：開 PR

- [ ] **Step 1：確認所有 commit 已推上 branch**

  ```bash
  git push origin issue-23-p5-2-mock-data-api
  ```

- [ ] **Step 2：開 PR**

  ```bash
  gh pr create \
    --repo MPinfo-Co/P1-code \
    --title "[P5-2] 前端串接 JWT 登入 API" \
    --base main \
    --head issue-23-p5-2-mock-data-api \
    --body "$(cat <<'EOF'
  ## 變更內容
  - 新增 `VITE_API_URL` 環境變數（`.env.example`）
  - `authStore.js`：login/logout 改為 async，存取 JWT token
  - `Login.jsx`：移除 mock 驗證，改為呼叫真實 API，input 改為 email
  - `App.jsx`：ProtectedRoute 改為判斷 `token !== null`
  ## 執行步驟
  1. 複製 `.env.example` 為 `.env.local`，設定 `VITE_API_URL`
  2. 確認後端已啟動（`uvicorn app.main:app --reload`）
  3. `npm run dev`
  4. 用 `admin@mpinfo.com.tw / @Admin1234` 登入測試

  ## 設計決策
  **VITE_API_URL 環境變數取代 proxy**：多客戶 + 多環境部署，proxy 只對本地有效，env var 才能擴展至 Vercel staging/production。

  ## 可調整設定
  | 設定 | 說明 |
  |---|---|
  | `VITE_API_URL` | 本地設在 `.env.local`，staging/production 在 Vercel Dashboard 設定 |

  ## 已知限制
  - 登入後 store 只存 email，姓名/角色待 `GET /api/users/me` 實作（P5-3）
  - Token 過期不會自動刷新，待後續規劃
  - `users.js` 仍被 Account.jsx、Role.jsx 使用，待這兩頁改用真實 API 後再刪除
  EOF
  )"
  ```
