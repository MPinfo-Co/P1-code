// src/queries/useUserOptionsQuery.ts
import { useQuery } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface UserOption {
  id: number
  name: string
}

function getToken() {
  return useAuthStore.getState().token
}

export function useUserOptionsQuery() {
  return useQuery<UserOption[]>({
    queryKey: ['userOptions'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/users/options`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('使用者選項載入失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}
