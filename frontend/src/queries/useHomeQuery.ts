// src/queries/useHomeQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface PartnerItem {
  id: number
  name: string
  description: string | null
  is_favorite: boolean
  sort_order: number
}

export interface TableItem {
  id: number
  name: string
  description: string | null
  is_favorite: boolean
  sort_order: number
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

export function useHomeTablesQuery() {
  return useQuery<TableItem[]>({
    queryKey: ['home-tables'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/home/tables`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢資料表清單失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useFavoriteToggle() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      item_type,
      item_id,
    }: {
      item_type: 'partner' | 'table'
      item_id: number
    }) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/home/favorite/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ item_type, item_id }),
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
      queryClient.invalidateQueries({ queryKey: ['home-tables'] })
    },
  })
}
