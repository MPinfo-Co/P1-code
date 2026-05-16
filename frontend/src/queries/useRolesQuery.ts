// src/queries/useRolesQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface FunctionOption {
  function_id: number
  function_code: string
}

export interface RoleUser {
  id: number
  name: string
  email: string
}

export interface RoleRow {
  name: string
  users: RoleUser[]
  functions: FunctionOption[]
  partner_ids?: number[]
  custom_table_ids?: number[]
}

export interface PaginatedRolesResponse {
  items: RoleRow[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface QueryParams {
  page?: number
  pageSize?: number
  keyword?: string
}

export interface CreateRolePayload {
  name: string
  member_ids?: number[]
  function_ids?: number[]
  partner_ids?: number[]
  custom_table_ids?: number[]
}

export interface UpdateRolePayload {
  name?: string
  member_ids?: number[]
  function_ids?: number[]
  partner_ids?: number[]
  custom_table_ids?: number[]
}

function getToken() {
  return useAuthStore.getState().token
}

export function useRolesQuery(params: QueryParams = {}) {
  const { page = 1, pageSize = 10, keyword } = params
  return useQuery<PaginatedRolesResponse>({
    queryKey: ['roles', { page, pageSize, keyword }],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      search.set('page', String(page))
      search.set('page_size', String(pageSize))
      if (keyword) search.set('keyword', keyword)
      const res = await fetch(`${BASE_URL}/roles?${search.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      if (json.items !== undefined) {
        return json as PaginatedRolesResponse
      }
      // Legacy flat array fallback
      const rawItems: RoleRow[] = json.data ?? json
      const items = Array.isArray(rawItems) ? rawItems : []
      return {
        items,
        total: items.length,
        page,
        page_size: pageSize,
        total_pages: Math.max(1, Math.ceil(items.length / pageSize)),
      }
    },
  })
}

export function useCreateRole() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateRolePayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/roles`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: payload.name,
          user_ids: payload.member_ids ?? [],
          function_ids: payload.function_ids ?? [],
          partner_ids: payload.partner_ids ?? [],
          custom_table_ids: payload.custom_table_ids ?? [],
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '新增失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] })
    },
  })
}

export function useUpdateRole() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ roleName, payload }: { roleName: string; payload: UpdateRolePayload }) => {
      const token = getToken()
      const body: Record<string, unknown> = {}
      if (payload.name !== undefined) body.name = payload.name
      if (payload.member_ids !== undefined) body.user_ids = payload.member_ids
      if (payload.function_ids !== undefined) body.function_ids = payload.function_ids
      if (payload.partner_ids !== undefined) body.partner_ids = payload.partner_ids
      if (payload.custom_table_ids !== undefined) body.custom_table_ids = payload.custom_table_ids
      const res = await fetch(`${BASE_URL}/roles/${encodeURIComponent(roleName)}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '更新失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] })
    },
  })
}

export function useDeleteRole() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (roleName: string) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/roles/${encodeURIComponent(roleName)}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '刪除失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] })
    },
  })
}
