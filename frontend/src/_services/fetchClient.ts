/**
 * 全域 401 攔截器 — 覆蓋 window.fetch
 *
 * 攔截條件：HTTP 401，排除登入 API 本身（POST /auth/login）
 * 攔截行為：立即清除 token → 導向 /login?expired=1
 *
 * 此模組在 main.jsx import 時自動生效，不需個別呼叫。
 */

import useAuthStore from '@/stores/authStore'

const _fetch = window.fetch.bind(window)

let isHandlingExpiry = false

function handleAuthExpiry() {
  if (isHandlingExpiry) return
  isHandlingExpiry = true

  localStorage.removeItem('mp-box-token')
  localStorage.removeItem('mp-box-user')
  useAuthStore.setState({ token: null, user: null })
  window.location.href = '/login?expired=1'
}

function isLoginRequest(input: RequestInfo | URL): boolean {
  const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
  return url.includes('/auth/login')
}

export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const response = await _fetch(input, init)

  if (response.status === 401 && !isLoginRequest(input)) {
    handleAuthExpiry()
  }

  return response
}

window.fetch = apiFetch

export default apiFetch
