// src/queries/useCustomTableQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface CustomTableRow {
  id: number
  name: string
  description: string
  field_count: number
  is_tool_referenced: boolean
}

export interface CustomTableField {
  field_name: string
  field_type: string
  description?: string
}

export interface CustomTableQueryParams {
  keyword?: string
}

export interface CreateCustomTablePayload {
  name: string
  description?: string
  fields: CustomTableField[]
}

export interface UpdateCustomTablePayload {
  name: string
  description?: string
  fields: CustomTableField[]
}

function getToken() {
  return useAuthStore.getState().token
}

export function useCustomTableQuery(params: CustomTableQueryParams = {}) {
  return useQuery<CustomTableRow[]>({
    queryKey: ['custom_table', params],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      if (params.keyword) search.set('keyword', params.keyword)
      const qs = search.toString()
      const res = await fetch(`${BASE_URL}/custom_table${qs ? `?${qs}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
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
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '新增失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom_table'] })
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
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '更新失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom_table'] })
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
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '刪除失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['custom_table'] })
      queryClient.invalidateQueries({ queryKey: ['custom_table_options'] })
    },
  })
}

// ── Detail (with fields) ─────────────────────────────────────────────────────

export interface CustomTableDetailField {
  id: number
  field_name: string
  field_type: string
  description: string | null
  sort_order: number
}

export interface CustomTableDetail {
  id: number
  name: string
  description: string | null
  has_records: boolean
  fields: CustomTableDetailField[]
}

export function useCustomTableByIdQuery(id: number | null) {
  return useQuery<CustomTableDetail>({
    queryKey: ['custom_table_detail', id],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
    enabled: !!id,
  })
}

// ── Records ──────────────────────────────────────────────────────────────────

export interface RecordFieldDef {
  field_name: string
  field_type: string
}

export interface CustomTableRecord {
  id: number
  data: Record<string, unknown>
  updated_by: number
  updated_at: string
}

export interface CustomTableRecordsOut {
  table_name: string
  fields: RecordFieldDef[]
  records: CustomTableRecord[]
}

export function useCustomTableRecordsQuery(tableId: number) {
  return useQuery<CustomTableRecordsOut>({
    queryKey: ['custom_table_records', tableId],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table/${tableId}/records`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
    enabled: !!tableId,
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
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '刪除失敗')
      }
    },
    onSuccess: (_data, { tableId }) => {
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
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '刪除失敗')
      }
    },
    onSuccess: (_data, tableId) => {
      queryClient.invalidateQueries({ queryKey: ['custom_table_records', tableId] })
    },
  })
}
