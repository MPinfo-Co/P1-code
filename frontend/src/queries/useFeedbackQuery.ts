// src/queries/useFeedbackQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface FeedbackRow {
  id: number
  user_name: string
  rating: number
  comment_summary: string | null
  created_at: string
}

export interface FeedbackListParams {
  rating?: number
}

export interface SubmitFeedbackPayload {
  rating: number
  comment?: string
}

function getToken() {
  return useAuthStore.getState().token
}

export function useFeedbackListQuery(params: FeedbackListParams = {}) {
  return useQuery<FeedbackRow[]>({
    queryKey: ['feedback', params],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      if (params.rating !== undefined) search.set('rating', String(params.rating))
      const qs = search.toString()
      const res = await fetch(`${BASE_URL}/api/feedback${qs ? `?${qs}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useSubmitFeedback() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: SubmitFeedbackPayload) => {
      const token = getToken()
      const body: Record<string, unknown> = { rating: payload.rating }
      if (payload.comment !== undefined && payload.comment !== '') {
        body.comment = payload.comment
      }
      const res = await fetch(`${BASE_URL}/api/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '提交失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feedback'] })
    },
  })
}
