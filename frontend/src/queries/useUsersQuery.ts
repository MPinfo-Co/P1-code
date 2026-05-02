// src/queries/useUsersQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface UserRow {
  email: string
  name: string
  roles: RoleOption[]
}

export interface RoleOption {
  id: number
  name: string
}

export interface QueryParams {
  role_id?: number
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
  return useQuery<UserRow[]>({
    queryKey: ['users', params],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      if (params.role_id !== undefined) search.set('role_id', String(params.role_id))
      if (params.keyword) search.set('keyword', params.keyword)
      const qs = search.toString()
      const res = await fetch(`${BASE_URL}/api/users${qs ? `?${qs}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateUserPayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/users`, {
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
      const res = await fetch(`${BASE_URL}/api/users/${encodeURIComponent(email)}`, {
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
      const res = await fetch(`${BASE_URL}/api/users/${encodeURIComponent(email)}`, {
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
