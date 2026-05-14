// src/queries/useExpertAnalysisQuery.ts
import { useQuery, useMutation } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

function authHeaders(): Record<string, string> {
  const token = useAuthStore.getState().token
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export type AnalysisStatus = 'idle' | 'running' | 'success' | 'failed'

export interface HaikuStatusSection {
  status: AnalysisStatus
  records_fetched: number | null
  error_message: string | null
}

export interface SonnetStatusSection {
  status: AnalysisStatus
  events_created: number | null
  error_message: string | null
}

export interface AnalysisStatusResponse {
  haiku: HaikuStatusSection
  sonnet: SonnetStatusSection
}

export interface TriggerPayload {
  time_from: string // ISO 8601
  time_to: string // ISO 8601
}

export function useAnalysisStatusQuery(enabled = true) {
  return useQuery<AnalysisStatusResponse>({
    queryKey: ['expert-analysis-status'],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/expert/analysis/status`, {
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      return json.data ?? json
    },
    enabled,
    refetchOnWindowFocus: false,
  })
}

export function useTriggerAnalysis() {
  return useMutation<{ message: string }, Error, TriggerPayload>({
    mutationFn: async (payload) => {
      const res = await fetch(`${BASE_URL}/expert/analysis/trigger`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (res.status === 409) {
        const json = await res.json().catch(() => ({}))
        throw Object.assign(new Error(json.detail ?? '彙整進行中，請稍後再試'), { status: 409 })
      }
      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.detail ?? `HTTP ${res.status}`)
      }
      return res.json()
    },
  })
}

export function useTriggerLogFetch() {
  return useMutation<{ message: string }, Error, TriggerPayload>({
    mutationFn: async (payload) => {
      const res = await fetch(`${BASE_URL}/expert/log/trigger`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (res.status === 409) {
        const json = await res.json().catch(() => ({}))
        throw Object.assign(new Error(json.detail ?? '抓 log 進行中，請稍後再試'), { status: 409 })
      }
      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.detail ?? `HTTP ${res.status}`)
      }
      return res.json()
    },
  })
}
