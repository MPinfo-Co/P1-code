// src/queries/useSettingsQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface SettingRow {
  param_type: string
  param_code: string
  param_value: string
}

export interface QueryParams {
  param_type?: string
}

export interface UpdateSettingPayload {
  param_value: string
}

function getToken() {
  return useAuthStore.getState().token
}

export function useSettingsQuery(params: QueryParams = {}) {
  return useQuery<SettingRow[]>({
    queryKey: ['settings', params],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      if (params.param_type && params.param_type !== 'all') {
        search.set('param_type', params.param_type)
      }
      const qs = search.toString()
      const res = await fetch(`${BASE_URL}/api/settings${qs ? `?${qs}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useParamTypeOptionsQuery() {
  return useQuery<string[]>({
    queryKey: ['settings-param-type-options'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/settings/options/param-types`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useUpdateSetting() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      paramCode,
      payload,
    }: {
      paramCode: string
      payload: UpdateSettingPayload
    }) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/settings/${encodeURIComponent(paramCode)}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ param_value: payload.param_value }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '更新失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
    },
  })
}
