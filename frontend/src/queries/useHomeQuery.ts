// src/queries/useHomeQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface PartnerItem {
  id: number
  name: string
  description: string | null
  is_favorite: boolean
}

function getToken() {
  return useAuthStore.getState().token
}

export function useHomePartnersQuery() {
  return useQuery<PartnerItem[]>({
    queryKey: ['home-partners'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/home/partners`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢夥伴清單失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useFavoriteToggle() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (partnerId: number) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/home/favorite/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ partner_id: partnerId }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '操作失敗')
      }
      const json = await res.json()
      return json.data ?? json
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['home-partners'] })
    },
  })
}
