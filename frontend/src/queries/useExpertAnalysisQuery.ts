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
  force?: boolean // log/trigger 專用：partial overlap 時帶 true 表示確認刪舊抓新
}

export interface OverlappingBatch {
  id: number
  time_from: string
  time_to: string
}

export interface TriggerLogError extends Error {
  status?: number
  overlap_type?: 'running' | 'partial'
  overlapping_batches?: OverlappingBatch[]
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
  return useMutation<{ message: string }, TriggerLogError, TriggerPayload>({
    mutationFn: async (payload) => {
      const res = await fetch(`${BASE_URL}/expert/log/trigger`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (res.status === 409) {
        const json = await res.json().catch(() => ({}))
        const detail = json.detail
        // 後端在重疊處理改成 dict detail（含 overlap_type / overlapping_batches）；
        // 沿用舊 string detail 也要相容
        const isObj = detail && typeof detail === 'object'
        const message = isObj ? (detail.message ?? '') : (detail ?? '抓 log 進行中，請稍後再試')
        throw Object.assign(new Error(message), {
          status: 409,
          overlap_type: isObj ? detail.overlap_type : undefined,
          overlapping_batches: isObj ? detail.overlapping_batches : undefined,
        }) as TriggerLogError
      }
      if (!res.ok) {
        const json = await res.json().catch(() => ({}))
        throw new Error(json.detail ?? `HTTP ${res.status}`)
      }
      return res.json()
    },
  })
}
