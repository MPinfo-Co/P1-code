// src/queries/useRoleOptionsQuery.ts
import { useQuery } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface RoleOption {
  id: number
  name: string
}

function getToken() {
  return useAuthStore.getState().token
}

export function useRoleOptionsQuery() {
  return useQuery<RoleOption[]>({
    queryKey: ['roleOptions'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/roles/options`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('角色選項載入失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}
