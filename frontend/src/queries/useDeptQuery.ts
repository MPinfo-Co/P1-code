// src/queries/useDeptQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface DeptRow {
  id: number
  name: string
  code: string
  parent_name: string | null
  head_name: string | null
  is_active: boolean
  level: number
}

export interface DeptOption {
  id: number
  name: string
}

export interface DeptMember {
  id: number
  name: string
}

export interface DeptQueryParams {
  keyword?: string
  page?: number
  page_size?: number
}

export interface DeptPageResult {
  items: DeptRow[]
  total: number
  page: number
  page_size: number
}

export interface CreateDeptPayload {
  name: string
  code: string
  parent_id?: number | null
  head_name?: string
}

export interface UpdateDeptPayload {
  name?: string
  code?: string
  parent_id?: number | null
  head_name?: string
}

function getToken() {
  return useAuthStore.getState().token
}

export function useDeptQuery(params: DeptQueryParams = {}) {
  return useQuery<DeptPageResult>({
    queryKey: ['dept', params],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      if (params.keyword) search.set('keyword', params.keyword)
      if (params.page !== undefined) search.set('page', String(params.page))
      if (params.page_size !== undefined) search.set('page_size', String(params.page_size))
      const qs = search.toString()
      const res = await fetch(`${BASE_URL}/api/dept${qs ? `?${qs}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useDeptOptionsQuery() {
  return useQuery<DeptOption[]>({
    queryKey: ['dept', 'options'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/dept/options`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢選項失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useDeptMembersQuery(deptId: number | null) {
  return useQuery<DeptMember[]>({
    queryKey: ['dept', 'members', deptId],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/dept/${deptId}/members`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢成員失敗')
      const json = await res.json()
      return json.data ?? json
    },
    enabled: deptId !== null,
  })
}

export function useCreateDept() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateDeptPayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/dept`, {
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
      queryClient.invalidateQueries({ queryKey: ['dept'] })
    },
  })
}

export function useUpdateDept() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: UpdateDeptPayload }) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/dept/${id}`, {
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
      queryClient.invalidateQueries({ queryKey: ['dept'] })
    },
  })
}

export function useToggleDept() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, isActive }: { id: number; isActive: boolean }) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/api/dept/${id}/toggle`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ is_active: isActive }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '操作失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dept'] })
    },
  })
}
