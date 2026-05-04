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
}

export interface QueryParams {
  keyword?: string
}

export interface CreateRolePayload {
  name: string
  member_ids?: number[]
  function_ids?: number[]
}

export interface UpdateRolePayload {
  name?: string
  member_ids?: number[]
  function_ids?: number[]
}

function getToken() {
  return useAuthStore.getState().token
}

export function useRolesQuery(params: QueryParams = {}) {
  return useQuery<RoleRow[]>({
    queryKey: ['roles', params],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      if (params.keyword) search.set('keyword', params.keyword)
      const qs = search.toString()
      const res = await fetch(`${BASE_URL}/roles${qs ? `?${qs}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

// export function useFunctionOptionsQuery() {
//   return useQuery<FunctionOption[]>({
//     queryKey: ['functionOptions'],
//     queryFn: async () => {
//       const token = getToken()
//       const res = await fetch(`${BASE_URL}/api/functions/options`, {
//         headers: { Authorization: `Bearer ${token}` },
//       })
//       if (!res.ok) throw new Error('功能選項載入失敗')
//       const json = await res.json()
//       return json.data ?? json
//     },
//   })
// }

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
