// src/queries/useToolsQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface BodyParam {
  param_name: string
  param_type: 'string' | 'number' | 'boolean' | 'object'
  is_required: boolean
  description: string
}

export interface ImageField {
  field_name: string
  field_type: 'string' | 'number'
  description: string
}

export type ToolType = 'external_api' | 'image_extract' | 'web_scraper'

export interface ToolRow {
  id: number
  name: string
  description: string
  tool_type: ToolType
  endpoint_url: string
  http_method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  auth_type: 'none' | 'api_key' | 'bearer'
  auth_header_name: string | null
  has_credential: boolean
  body_params?: BodyParam[]
  image_fields?: ImageField[]
}

export interface ToolQueryParams {
  keyword?: string
}

export interface CreateToolPayload {
  name: string
  description: string
  tool_type: ToolType
  endpoint_url?: string
  auth_type?: 'none' | 'api_key' | 'bearer'
  auth_header_name?: string | null
  credential?: string
  http_method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body_params?: BodyParam[]
  image_fields?: ImageField[]
}

export interface UpdateToolPayload {
  name: string
  description: string
  endpoint_url?: string
  auth_type?: 'none' | 'api_key' | 'bearer'
  auth_header_name?: string | null
  credential?: string
  http_method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body_params?: BodyParam[]
  image_fields?: ImageField[]
}

export interface TestToolPayload {
  endpoint_url: string
  auth_type: 'none' | 'api_key' | 'bearer'
  auth_header_name?: string | null
  credential?: string
  http_method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body_params_values?: Record<string, unknown>
  tool_id?: number
}

export interface TestToolResult {
  http_status: number
  response_body: unknown
}

function getToken() {
  return useAuthStore.getState().token
}

export function useToolsQuery(params: ToolQueryParams = {}) {
  return useQuery<ToolRow[]>({
    queryKey: ['tools', params],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      if (params.keyword) search.set('keyword', params.keyword)
      const qs = search.toString()
      const res = await fetch(`${BASE_URL}/tool${qs ? `?${qs}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useCreateTool() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateToolPayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/tool`, {
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
      queryClient.invalidateQueries({ queryKey: ['tools'] })
    },
  })
}

export function useUpdateTool() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: UpdateToolPayload }) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/tool/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '更新失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tools'] })
    },
  })
}

export function useDeleteTool() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/tool/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '刪除失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tools'] })
    },
  })
}

export function useTestTool() {
  return useMutation({
    mutationFn: async (payload: TestToolPayload): Promise<TestToolResult> => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/tool/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '測試失敗')
      }
      const json = await res.json()
      return json.data ?? json
    },
  })
}
