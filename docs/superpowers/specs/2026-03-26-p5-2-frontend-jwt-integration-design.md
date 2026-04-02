# P5-2 前端串接 JWT API 設計文件

**日期**：2026-03-26
**範圍**：前端 Login.jsx + authStore.js 改為呼叫真實後端 JWT API

---

## 背景

目前 Login.jsx 使用 mock 驗證（對照 `src/data/users.js`，密碼固定 123）。P4-3 已完成後端 `POST /api/auth/login`，本 issue 目標是將前端登入改為呼叫真實 API。

---

## 部署架構

- 前端：Vercel（多客戶，每客戶獨立 project）
- 後端：Railway（FastAPI + PostgreSQL）
- 環境：development / staging / production 三層

---

## 決策：API URL 管理方式

採用 **`VITE_API_URL` 環境變數**，各環境各自設定，不使用 Vite proxy。

理由：
- 多客戶部署時，每個 Vercel project 設定自己的後端 URL
- Vercel 原生支援 per-environment env var（Dashboard > Settings > Environment Variables）
- Proxy 只對本地有效，無法擴展至多環境

**各環境設定方式：**
- **development**：本地 `.env.local`（不進 git）
- **staging / production**：在 Vercel Dashboard 的 Environment Variables 設定，不需建立 `.env.staging` 或 `.env.production` 檔案

---

## 變更範圍

### 新增檔案

| 檔案 | 說明 |
|---|---|
| `frontend/.env.local` | 本地開發用，不進 git |
| `frontend/.env.example` | 範本，進 git |

`.env.local` 內容：
```
VITE_API_URL=http://localhost:8000
```

`.env.example` 內容（staging/production 在 Vercel Dashboard 設定，不需建 .env.production）：
```
# 本地開發預設值，staging/production 在 Vercel Dashboard 設定
VITE_API_URL=http://localhost:8000
```

確認 `frontend/.gitignore` 包含 `.env.local`。

---

### authStore.js 改動

**Store state shape：**
```js
{
  token: string | null,  // 從 localStorage.getItem('mp-box-token') 同步初始化
  user: { email: string } | null,  // 刷新後為 null，等 GET /api/users/me 完成後補齊
}
```

> **注意**：`token` 初始化為同步 `localStorage.getItem`，確保 ProtectedRoute 第一次 render 時 token 已可用，不會閃登出。`user` 刷新後為 null 是刻意決策——使用者資訊（姓名、角色）等 P5-3 實作 `GET /api/users/me` 後補齊。任何顯示 `user` 資訊的 UI 元件需做 null guard。

**具體改動：**

1. 新增 `token` 欄位，初始值從 `localStorage.getItem('mp-box-token')` 同步讀取
2. `login(email, password)` 改為 async：
   ```js
   const res = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/login`, {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ email, password }),
   })
   if (res.status === 401) throw new Error('帳號或密碼錯誤')
   if (!res.ok) throw new Error('伺服器錯誤，請稍後再試')
   const { access_token } = await res.json()
   localStorage.setItem('mp-box-token', access_token)
   set({ token: access_token, user: { email } })
   ```
3. `logout()` 改為 async：
   ```js
   await fetch(`${import.meta.env.VITE_API_URL}/api/auth/logout`, {
     method: 'POST',
     headers: { 'Authorization': `Bearer ${get().token}` },
   }).catch((err) => { console.warn('[logout] backend call failed:', err) })
   localStorage.removeItem('mp-box-token')
   set({ token: null, user: null })
   ```

---

### Login.jsx 改動

1. input 欄位從「姓名或 Email」改為 Email（`type="email"`）
2. `handleSubmit` 改為 async
3. 呼叫 `authStore.login(email, password)`，catch error message 後顯示給使用者
4. 移除 `import { users } from '../../data/users'`（`users.js` 檔案本身保留，待 P5-2 驗證完成後獨立 commit 移除）

---

### ProtectedRoute 行為

目前 ProtectedRoute 判斷 `user !== null`，改為判斷 `token !== null`。由於 store 以同步 `localStorage.getItem` 初始化，刷新後 token 立即可用，不會觸發閃登出。

---

## API 規格（後端已實作）

```
POST /api/auth/login
Content-Type: application/json

Request:  { "email": "string", "password": "string" }
Response: { "access_token": "string", "token_type": "bearer" }

Error 401: 帳號或密碼錯誤
```

```
POST /api/auth/logout
Authorization: Bearer <token>

Response: { "message": "logged out" }
```

---

## 已知限制（不在本 issue 範圍）

- 其他 API call 帶 token（Authorization header）→ P5-3
- `GET /api/users/me`：取得完整使用者資訊（姓名、角色）存入 store → P5-3
- Token 過期自動刷新 → 待規劃
- `users.js` mock 資料清理 → P5-2 驗證完成後移除
