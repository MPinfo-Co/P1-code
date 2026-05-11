// src/queries/useUsersQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface UserRow {
  email: string
  name: string
  roles: RoleOption[]
  role_ids?: number[]
}

export interface RoleOption {
  id: number
  name: string
}

export interface PaginatedUsersResponse {
  items: UserRow[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface QueryParams {
  page?: number
  pageSize?: number
  roleFilter?: number
  keyword?: string
}

export interface CreateUserPayload {
  name: string
  email: string
  password: string
  role_ids: number[]
}

export interface UpdateUserPayload {
  name?: string
  password?: string
  role_ids?: number[]
}

function getToken() {
  return useAuthStore.getState().token
}

export function useUsersQuery(params: QueryParams = {}) {
  const { page = 1, pageSize = 10, roleFilter, keyword } = params
  return useQuery<PaginatedUsersResponse>({
    queryKey: ['users', { page, pageSize, roleFilter, keyword }],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      search.set('page', String(page))
      search.set('page_size', String(pageSize))
      if (roleFilter !== undefined) search.set('role_id', String(roleFilter))
      if (keyword) search.set('keyword', keyword)
      const res = await fetch(`${BASE_URL}/user?${search.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      if (json.items !== undefined) {
        return json as PaginatedUsersResponse
      }
      // Legacy flat array fallback
      const rawItems: UserRow[] = json.data ?? json
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

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateUserPayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/user`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: payload.name,
          email: payload.email,
          password: payload.password,
          role_ids: payload.role_ids,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '新增失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}

export function useUpdateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ email, payload }: { email: string; payload: UpdateUserPayload }) => {
      const token = getToken()
      const body: Record<string, unknown> = {}
      if (payload.name !== undefined) body.name = payload.name
      if (payload.password !== undefined) body.password = payload.password
      if (payload.role_ids !== undefined) body.role_ids = payload.role_ids
      const res = await fetch(`${BASE_URL}/user/${encodeURIComponent(email)}`, {
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
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}

export function useDeleteUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (email: string) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/user/${encodeURIComponent(email)}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '刪除失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}
