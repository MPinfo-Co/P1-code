// src/queries/useCustomTableQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

// ── Types ──

export interface CustomTableField {
  field_name: string
  field_type: 'string' | 'number'
  description: string
}

export interface CustomTableFieldDef {
  id: number
  field_name: string
  field_type: string
  description: string | null
  sort_order: number
}

export interface CustomTableRecord {
  id: number
  data: Record<string, unknown>
  created_at: string
}

export interface CustomTableRecordsData {
  fields: CustomTableFieldDef[]
  records: CustomTableRecord[]
}

export interface CustomTableRow {
  id: number
  name: string
  description: string
  field_count: number
}

export interface CustomTableOption {
  id: number
  name: string
  fields: CustomTableField[]
}

export interface CustomTableQueryParams {
  keyword?: string
}

export interface CreateCustomTablePayload {
  name: string
  description: string
  fields: CustomTableField[]
}

export interface UpdateCustomTablePayload {
  name: string
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
    const detail = err.detail
    if (typeof detail === 'string') throw new Error(detail)
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as Record<string, unknown>
      throw new Error(String(first.msg ?? '驗證失敗'))
    }
    throw new Error(String(err.message ?? '操作失敗'))
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

export function useCustomTableRecordsQuery(tableId: number | null) {
  return useQuery<CustomTableRecordsData>({
    queryKey: ['custom_table_records', tableId],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table/${tableId}/records`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '查詢失敗')
      }
      return res.json()
    },
    enabled: tableId !== null,
  })
}

export function useDeleteCustomTableRecord() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ tableId, recordId }: { tableId: number; recordId: number }) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table/${tableId}/records/${recordId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      await handleResponse(res)
    },
    onSuccess: (_, { tableId }) => {
      queryClient.invalidateQueries({ queryKey: ['custom_table_records', tableId] })
    },
  })
}

export function useDeleteAllCustomTableRecords() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (tableId: number) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table/${tableId}/records`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      await handleResponse(res)
    },
    onSuccess: (_, tableId) => {
      queryClient.invalidateQueries({ queryKey: ['custom_table_records', tableId] })
    },
  })
}
