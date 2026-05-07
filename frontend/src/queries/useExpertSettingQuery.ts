// src/queries/useExpertSettingQuery.ts
import { useQuery, useMutation } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface ExpertSetting {
  is_enabled: boolean
  frequency: 'daily' | 'weekly' | 'manual'
  schedule_time: string | null
  weekday: number | null
  ssb_host: string | null
  ssb_port: number | null
  ssb_logspace: string | null
  ssb_username: string | null
  ssb_password: string | null
}

export interface SaveExpertSettingPayload {
  is_enabled: boolean
  frequency: string
  schedule_time: string | null
  weekday: number | null
  ssb_host: string
  ssb_port: number
  ssb_logspace: string
  ssb_username: string
  ssb_password: string
}

export interface SsbTestPayload {
  host: string
  port: number
  logspace: string
  username: string
  password: string
}

function getToken() {
  return useAuthStore.getState().token
}

export function useExpertSettingQuery() {
  return useQuery<ExpertSetting>({
    queryKey: ['expertSetting'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/expert/settings`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '查詢失敗')
      }
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useSaveExpertSetting() {
  return useMutation({
    mutationFn: async (payload: SaveExpertSettingPayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/expert/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '儲存失敗')
      }
      const json = await res.json()
      return json
    },
  })
}

export function useSsbTest() {
  return useMutation({
    mutationFn: async (payload: SsbTestPayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/expert/ssb-test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '連線失敗')
      }
      const json = await res.json()
      return json
    },
  })
}
