// src/stores/authStore.ts
import { create } from 'zustand'

const BASE_URL = import.meta.env.VITE_API_URL as string

export interface AuthUser {
  id?: number
  name?: string
  email: string
  functions?: string[]
}

interface AuthState {
  token: string | null
  user: AuthUser | null
}

interface AuthActions {
  fetchMe: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

type AuthStore = AuthState & AuthActions

const useAuthStore = create<AuthStore>((set, get) => ({
  token: localStorage.getItem('mp-box-token') || null,
  user: null,

  fetchMe: async () => {
    const token = get().token
    if (!token) return
    try {
      const res = await fetch(`${BASE_URL}/user/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) return
      const data = await res.json()
      set({ user: data.data })
    } catch (err) {
      console.warn('[fetchMe] failed:', err)
    }
  },

  login: async (email, password) => {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (res.status === 401) throw new Error('帳號或密碼錯誤')
    if (!res.ok) throw new Error('伺服器錯誤，請稍後再試')
    const { access_token } = await res.json()
    localStorage.setItem('mp-box-token', access_token)
    set({ token: access_token, user: { email } })
    await useAuthStore.getState().fetchMe()
  },

  logout: async () => {
    await fetch(`${BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${get().token}` },
    }).catch((err) => {
      console.warn('[logout] backend call failed:', err)
    })
    localStorage.removeItem('mp-box-token')
    localStorage.removeItem('mp-box-user')
    set({ token: null, user: null })
  },
}))

export function useAuth() {
  return useAuthStore()
}

export default useAuthStore
