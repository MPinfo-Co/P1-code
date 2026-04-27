import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

// ── Data interfaces ──────────────────────────────────────────────

export interface RoleOption {
  id: number
  name: string
}

export interface UserRow {
  email: string
  name: string
  is_active: boolean
  roles: RoleOption[]
}

export interface UserQueryParams {
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

// ── Helper ────────────────────────────────────────────────────────

function authHeaders(): Record<string, string> {
  const token = useAuthStore.getState().token
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

// ── Users query ───────────────────────────────────────────────────

export function useUsersQuery(params: UserQueryParams = {}) {
  return useQuery<UserRow[]>({
    queryKey: ['users', params],
    queryFn: async () => {
      const url = new URL(`${BASE_URL}/api/users`)
      if (params.role_id) url.searchParams.set('role_id', String(params.role_id))
      if (params.keyword) url.searchParams.set('keyword', params.keyword)

      const res = await fetch(url.toString(), { headers: authHeaders() })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.message ?? `HTTP ${res.status}`)
      }
      const json = await res.json()
      return json.data ?? json
    },
  })
}

// ── Roles query（供 Form 取得角色選項） ──────────────────────────

export function useRolesOptionsQuery() {
  return useQuery<RoleOption[]>({
    queryKey: ['roles-options'],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/api/roles`, { headers: authHeaders() })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.message ?? `HTTP ${res.status}`)
      }
      const json = await res.json()
      const list: Array<{ id: number; name: string }> = json.data ?? json
      return list.map((r) => ({ id: r.id, name: r.name }))
    },
  })
}

// ── Create user mutation ──────────────────────────────────────────

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateUserPayload) => {
      const res = await fetch(`${BASE_URL}/api/users`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.message ?? `HTTP ${res.status}`)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}

// ── Update user mutation ──────────────────────────────────────────

export function useUpdateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ email, payload }: { email: string; payload: UpdateUserPayload }) => {
      const res = await fetch(`${BASE_URL}/api/users/${encodeURIComponent(email)}`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.message ?? `HTTP ${res.status}`)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}

// ── Delete user mutation ──────────────────────────────────────────

export function useDeleteUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (email: string) => {
      const res = await fetch(`${BASE_URL}/api/users/${encodeURIComponent(email)}`, {
        method: 'DELETE',
        headers: authHeaders(),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.message ?? `HTTP ${res.status}`)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })
}
