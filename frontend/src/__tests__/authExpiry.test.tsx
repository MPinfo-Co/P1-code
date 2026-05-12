/**
 * 前端整合測試：認證失效攔截器 + 登入頁過期提示
 *
 * 對應 TestSpec：
 *   T1 — 401 攔截器立即清除 token 並導向 /login?expired=1
 *   T2 — 登入頁 expired=1 時顯示提示
 *   T3 — 登入頁正常載入不顯示提示
 *   T4 — 登入 API 自身的 401 不觸發攔截器
 *   T5 — 非 401 錯誤不觸發攔截器
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Login from '../pages/Login/Login'
import { apiFetch } from '../_services/fetchClient'

// -------------------------------------------------------------------
// 共用 helper
// -------------------------------------------------------------------

function renderLogin(initialEntries: string[] = ['/login']) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <Login />
      </MemoryRouter>
    </QueryClientProvider>
  )
}

// -------------------------------------------------------------------
// T2 / T3：登入頁過期提示
// -------------------------------------------------------------------

describe('登入頁過期提示', () => {
  it('T2 — URL 含 expired=1 時，顯示「登入已過期，請重新登入」', () => {
    /**對應 T2 */
    renderLogin(['/login?expired=1'])
    expect(screen.getByTestId('expired-notice')).toBeInTheDocument()
    expect(screen.getByTestId('expired-notice')).toHaveTextContent('登入已過期，請重新登入')
  })

  it('T3 — URL 不含 expired=1 時，不顯示過期提示', () => {
    /**對應 T3 */
    renderLogin(['/login'])
    expect(screen.queryByTestId('expired-notice')).not.toBeInTheDocument()
  })

  it('T3b — URL 含無關 query string 時，不顯示過期提示', () => {
    /**對應 T3 */
    renderLogin(['/login?redirect=/dashboard'])
    expect(screen.queryByTestId('expired-notice')).not.toBeInTheDocument()
  })

  it('表單欄位在 expired=1 時仍正常可用', () => {
    /**對應 T2 */
    renderLogin(['/login?expired=1'])
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/密碼/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /登入系統/i })).toBeEnabled()
  })
})

// -------------------------------------------------------------------
// T1 / T4 / T5：401 攔截器行為
// -------------------------------------------------------------------

describe('全域 401 攔截器', () => {
  let locationHref: string

  beforeEach(() => {
    locationHref = 'http://localhost/dashboard'
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { ...window.location, href: locationHref },
    })
    localStorage.setItem('mp-box-token', 'test-token')
    localStorage.setItem('mp-box-user', JSON.stringify({ id: 1 }))
  })

  afterEach(() => {
    vi.restoreAllMocks()
    localStorage.removeItem('mp-box-token')
    localStorage.removeItem('mp-box-user')
  })

  it('T1 — 收到 401 時，立即清除 token 並導向 /login?expired=1', async () => {
    /**對應 T1 */
    const mockFetch = vi.fn().mockResolvedValue(new Response(null, { status: 401 }))
    vi.stubGlobal('fetch', mockFetch)

    await apiFetch('http://localhost:8000/user')

    expect(localStorage.getItem('mp-box-token')).toBeNull()
    expect(localStorage.getItem('mp-box-user')).toBeNull()
    expect(window.location.href).toBe('/login?expired=1')

    vi.unstubAllGlobals()
  })

  it('T4 — 登入 API 回傳 401 時，不觸發全域攔截器', async () => {
    /**對應 T4 */
    const mockFetch = vi.fn().mockResolvedValue(new Response(null, { status: 401 }))
    vi.stubGlobal('fetch', mockFetch)

    await apiFetch('http://localhost:8000/auth/login')

    expect(localStorage.getItem('mp-box-token')).toBe('test-token')
    expect(window.location.href).toBe(locationHref)

    vi.unstubAllGlobals()
  })

  it('T5 — 非 401 錯誤（如 403）不觸發攔截器', async () => {
    /**對應 T5 */
    const mockFetch = vi.fn().mockResolvedValue(new Response(null, { status: 403 }))
    vi.stubGlobal('fetch', mockFetch)

    await apiFetch('http://localhost:8000/user')

    expect(localStorage.getItem('mp-box-token')).toBe('test-token')
    expect(window.location.href).toBe(locationHref)

    vi.unstubAllGlobals()
  })
})
