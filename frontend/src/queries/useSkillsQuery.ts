// src/queries/useSkillsQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface BodyParam {
  param_name: string
  param_type: 'string' | 'number' | 'boolean' | 'object'
  is_required: boolean
  description: string
}

export interface SkillRow {
  id: number
  name: string
  description: string
  endpoint_url: string
  http_method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  auth_type: 'none' | 'api_key' | 'bearer'
  auth_header_name: string | null
  has_credential: boolean
  body_params?: BodyParam[]
}

export interface SkillQueryParams {
  keyword?: string
}

export interface CreateSkillPayload {
  name: string
  description: string
  endpoint_url: string
  auth_type: 'none' | 'api_key' | 'bearer'
  auth_header_name?: string | null
  credential?: string
  http_method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body_params: BodyParam[]
}

export interface UpdateSkillPayload {
  name: string
  description: string
  endpoint_url: string
  auth_type: 'none' | 'api_key' | 'bearer'
  auth_header_name?: string | null
  credential?: string
  http_method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body_params: BodyParam[]
}

export interface TestSkillPayload {
  endpoint_url: string
  auth_type: 'none' | 'api_key' | 'bearer'
  auth_header_name?: string | null
  credential?: string
  http_method: 'GET' | 'POST' | 'PUT' | 'DELETE'
  body_params_values?: Record<string, unknown>
  skill_id?: number
}

export interface TestSkillResult {
  http_status: number
  response_body: unknown
}

function getToken() {
  return useAuthStore.getState().token
}

export function useSkillsQuery(params: SkillQueryParams = {}) {
  return useQuery<SkillRow[]>({
    queryKey: ['skills', params],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      if (params.keyword) search.set('keyword', params.keyword)
      const qs = search.toString()
      const res = await fetch(`${BASE_URL}/skill${qs ? `?${qs}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useCreateSkill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateSkillPayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/skill`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '新增失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
    },
  })
}

export function useUpdateSkill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: UpdateSkillPayload }) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/skill/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '更新失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
    },
  })
}

export function useDeleteSkill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/skill/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '刪除失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] })
    },
  })
}

export function useTestSkill() {
  return useMutation({
    mutationFn: async (payload: TestSkillPayload): Promise<TestSkillResult> => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/skill/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '測試失敗')
      }
      const json = await res.json()
      return json.data ?? json
    },
  })
}
