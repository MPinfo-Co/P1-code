/**
 * 全域 fetch wrapper — 統一攔截 401 認證失效
 *
 * 攔截條件：
 *   - HTTP 401
 *   - 排除登入 API 本身（POST /auth/login）
 *
 * 攔截行為：
 *   1. 透過 uiStore 設定全域通知訊息「登入已過期，請重新登入」
 *   2. 約 2 秒後：清除 token → 導向 /login?expired=1
 */

import useAuthStore from '@/stores/authStore'
import useUiStore from '@/stores/uiStore'

// 避免重複觸發（例如頁面上同時有多個 API 請求都 401）
let isHandlingExpiry = false

const EXPIRY_MESSAGE = '登入已過期，請重新登入'

/**
 * 透過 uiStore 通知 App 層顯示「登入已過期」提示。
 */
function notifyAuthExpired() {
  useUiStore.getState().setGlobalNotice(EXPIRY_MESSAGE)
}

/**
 * 執行登入失效後的清理與跳轉
 */
function handleAuthExpiry() {
  if (isHandlingExpiry) return
  isHandlingExpiry = true

  notifyAuthExpired()

  setTimeout(() => {
    // 直接清除本地 token，不呼叫後端 logout API（避免再觸發 401）
    localStorage.removeItem('mp-box-token')
    localStorage.removeItem('mp-box-user')
    useAuthStore.setState({ token: null, user: null })
    useUiStore.getState().clearGlobalNotice()
    isHandlingExpiry = false
    window.location.href = '/login?expired=1'
  }, 2000)
}

/**
 * 是否為登入 API（排除不觸發全域攔截器）
 */
function isLoginRequest(input: RequestInfo | URL): boolean {
  const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
  return url.includes('/auth/login')
}

/**
 * 全域 fetch wrapper
 * 使用方式同 fetch()，直接替換既有呼叫。
 */
export async function apiFetch(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const response = await fetch(input, init)

  if (response.status === 401 && !isLoginRequest(input)) {
    handleAuthExpiry()
    // 回傳原始 response，讓呼叫端可以選擇自行處理（會看到 401）
    return response
  }

  return response
}

export default apiFetch
