// src/queries/useCustomTableQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

// ── Types ──

export interface CustomTableField {
  field_name: string
  field_type: 'string' | 'number'
  field_description: string
}

export interface CustomTableRow {
  id: number
  table_name: string
  description: string
  field_count: number
}

export interface CustomTableOption {
  id: number
  table_name: string
  fields: CustomTableField[]
}

export interface CustomTableQueryParams {
  keyword?: string
}

export interface CreateCustomTablePayload {
  table_name: string
  description: string
  fields: CustomTableField[]
}

export interface UpdateCustomTablePayload {
  table_name: string
  description: string
  fields: CustomTableField[]
}

// ── Helpers ──

function getToken() {
  return useAuthStore.getState().token
}

async function handleResponse(res: Response) {
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? err.message ?? '操作失敗')
  }
}

// ── Hooks ──

export function useCustomTablesQuery(params: CustomTableQueryParams = {}) {
  return useQuery<CustomTableRow[]>({
    queryKey: ['custom_tables', params],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      if (params.keyword) search.set('keyword', params.keyword)
      const qs = search.toString()
      const res = await fetch(`${BASE_URL}/custom_table${qs ? `?${qs}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '查詢失敗')
      }
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useCustomTableOptionsQuery() {
  return useQuery<CustomTableOption[]>({
    queryKey: ['custom_table_options'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table/options`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '查詢失敗')
      }
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useCreateCustomTable() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateCustomTablePayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      await handleResponse(res)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom_tables'] })
      queryClient.invalidateQueries({ queryKey: ['custom_table_options'] })
    },
  })
}

export function useUpdateCustomTable() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: UpdateCustomTablePayload }) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      })
      await handleResponse(res)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom_tables'] })
      queryClient.invalidateQueries({ queryKey: ['custom_table_options'] })
    },
  })
}

export function useDeleteCustomTable() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      await handleResponse(res)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom_tables'] })
      queryClient.invalidateQueries({ queryKey: ['custom_table_options'] })
    },
  })
}
