// src/queries/useFunctionOptionsQuery.ts
import { useQuery } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface FunctionOption {
  function_id: number
  function_name: string
}

function getToken() {
  return useAuthStore.getState().token
}

export function useFunctionOptionsQuery() {
  return useQuery<FunctionOption[]>({
    queryKey: ['functionOptions'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/functions/options`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('功能選項載入失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}
