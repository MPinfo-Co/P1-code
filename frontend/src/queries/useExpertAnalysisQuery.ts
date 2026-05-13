// src/queries/useExpertAnalysisQuery.ts
import { useQuery, useMutation } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

function authHeaders(): Record<string, string> {
  const token = useAuthStore.getState().token
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export type AnalysisStatus = 'idle' | 'running' | 'success' | 'failed'

export interface AnalysisStatusResponse {
  status: AnalysisStatus
  events_created: number | null
  error_message: string | null
}

export function useAnalysisStatusQuery(enabled = true) {
  return useQuery<AnalysisStatusResponse>({
    queryKey: ['expert-analysis-status'],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/expert/analysis/status`, {
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json()
    },
    enabled,
    refetchOnWindowFocus: false,
  })
}

export function useTriggerAnalysis() {
  return useMutation<{ message: string }, Error, void>({
    mutationFn: async () => {
      const res = await fetch(`${BASE_URL}/expert/analysis/trigger`, {
        method: 'POST',
        headers: authHeaders(),
      })
      if (res.status === 409) {
        const json = await res.json().catch(() => ({}))
        throw Object.assign(new Error(json.message ?? '分析進行中，請稍後再試'), { status: 409 })
      }
      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.message ?? `HTTP ${res.status}`)
      }
      return res.json()
    },
  })
}
