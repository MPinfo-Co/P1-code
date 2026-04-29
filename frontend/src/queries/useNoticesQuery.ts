// src/queries/useNoticesQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface NoticeItem {
  id: number
  title: string
  expires_at: string
}

export interface NoticesListResult {
  data: NoticeItem[]
  can_manage: boolean
}

export interface CreateNoticePayload {
  title: string
  content: string
  expires_at: string
}

function getToken() {
  return useAuthStore.getState().token
}

export function useNoticesQuery() {
  return useQuery<NoticesListResult>({
    queryKey: ['notices'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/notices`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢公告失敗')
      const json = await res.json()
      return {
        data: json.data ?? [],
        can_manage: json.can_manage ?? false,
      }
    },
  })
}

export function useCreateNotice() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateNoticePayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/notices`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '新增失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notices'] })
    },
  })
}
