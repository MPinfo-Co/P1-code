// src/stores/authStore.js
import { create } from 'zustand'

const useAuthStore = create((set) => ({
  user: (() => {
    const stored = localStorage.getItem('mp-box-user')
    return stored ? JSON.parse(stored) : null
  })(),

  login: (username, role) => {
    const userData = { username, role }
    localStorage.setItem('mp-box-user', JSON.stringify(userData))
    set({ user: userData })
  },

  logout: () => {
    localStorage.removeItem('mp-box-user')
    set({ user: null })
  },
}))

export function useAuth() {
  return useAuthStore()
}

export default useAuthStore
