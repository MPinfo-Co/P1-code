// src/stores/authStore.js
import { create } from 'zustand'

const BASE_URL = import.meta.env.BACKEND_URL

interface UserState {
  token: string | null,
  userId: number | null,
  userName: string | null,
  email: string | null,
  password: string | null

  login: (email: string, password: string) => void,
  logout: (userId: number) => void
}

const useAuthStore = create<UserState>((set, get) => (
  {
    token: null,
    userId: null,
    userName: null,
    email: null,
    password: null,

    login:(email: string, password: string) => {
      const res = await fetch(`${BASE_URL}/auth/login`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        }
      )
      if (res.status == 401) throw new Error("帳號/密碼錯誤");
      if (!res.ok) throw new Error("未知錯誤，請稍後再試")

    },
    logout:(userId: number) => {
      console.log('pass here')
    }
  }
))

export default useAuthStore
