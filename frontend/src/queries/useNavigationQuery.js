import { useQuery } from '@tanstack/react-query'
import useAuthStore from '../stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export function useNavigationQuery() {
  const token = useAuthStore((state) => state.token)
  return useQuery({
    queryKey: ['navigation'],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/navigation`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('導覽資料載入失敗')
      const json = await res.json()
      return json.data ?? json
    },
    enabled: !!token,
    staleTime: 5 * 60 * 1000,
  })
}
