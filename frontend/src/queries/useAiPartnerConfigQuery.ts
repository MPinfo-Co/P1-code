// src/queries/useAiPartnerConfigQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface AiPartnerRow {
  id: number
  name: string
  description: string | null
  is_enabled: boolean
  role_definition: string | null
  behavior_limit: string | null
  tool_ids: number[]
}

export interface ToolOption {
  id: number
  name: string
  description: string
}

export interface AiPartnerQueryParams {
  keyword?: string
}

export interface CreateAiPartnerPayload {
  name: string
  description?: string
  role_definition?: string
  behavior_limit?: string
  tool_ids?: number[]
}

export interface UpdateAiPartnerPayload {
  name: string
  description?: string
  role_definition?: string
  behavior_limit?: string
  tool_ids?: number[]
  is_enabled?: boolean
}

function getToken() {
  return useAuthStore.getState().token
}

export function useAiPartnerConfigQuery(params: AiPartnerQueryParams = {}) {
  return useQuery<AiPartnerRow[]>({
    queryKey: ['ai-partner-config', params],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      if (params.keyword) search.set('keyword', params.keyword)
      const qs = search.toString()
      const res = await fetch(`${BASE_URL}/ai-partner-config${qs ? `?${qs}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useToolOptionsQuery() {
  return useQuery<ToolOption[]>({
    queryKey: ['tool-options'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/tool/options`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢工具選項失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useCreateAiPartner() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateAiPartnerPayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/ai-partner-config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: payload.name,
          description: payload.description,
          role_definition: payload.role_definition,
          behavior_limit: payload.behavior_limit,
          tool_ids: payload.tool_ids,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '新增失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-partner-config'] })
    },
  })
}

export function useUpdateAiPartner() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: UpdateAiPartnerPayload }) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/ai-partner-config/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: payload.name,
          description: payload.description,
          role_definition: payload.role_definition,
          behavior_limit: payload.behavior_limit,
          tool_ids: payload.tool_ids,
          is_enabled: payload.is_enabled,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '更新失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-partner-config'] })
    },
  })
}

export function useDeleteAiPartner() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/ai-partner-config/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '刪除失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-partner-config'] })
    },
  })
}
