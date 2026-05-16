// src/queries/useCustomTableDataInputQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface CustomTableOption {
  id: number
  name: string
  description: string
}

export interface CustomTableField {
  id: number
  field_name: string
  field_type: 'string' | 'number'
  sort_order: number
}

export interface CustomTableRecord {
  id: number
  data: Record<string, unknown>
  updated_at: string
}

export interface CustomTableRecordsResponse {
  fields: CustomTableField[]
  records: CustomTableRecord[]
}

function getToken() {
  return useAuthStore.getState().token
}

export function useCustomTableDataInputListQuery() {
  return useQuery<CustomTableOption[]>({
    queryKey: ['custom_table_data_input', 'tables'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table_data_input/tables`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return (json.data ?? json) as CustomTableOption[]
    },
  })
}

export function useCustomTableDataInputRecordsQuery(tableId: number | null) {
  return useQuery<CustomTableRecordsResponse>({
    queryKey: ['custom_table_data_input', 'records', tableId],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table_data_input/tables/${tableId}/records`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return (json.data ?? json) as CustomTableRecordsResponse
    },
    enabled: tableId !== null,
  })
}

export function useAddCustomTableRecord() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ tableId, data }: { tableId: number; data: Record<string, unknown> }) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table_data_input/tables/${tableId}/records`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ data }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '新增失敗')
      }
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['custom_table_data_input', 'records', variables.tableId],
      })
    },
  })
}

export function useDeleteCustomTableRecord() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ tableId, recordId }: { tableId: number; recordId: number }) => {
      const token = getToken()
      const res = await fetch(
        `${BASE_URL}/custom_table_data_input/tables/${tableId}/records/${recordId}`,
        {
          method: 'DELETE',
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '刪除失敗')
      }
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['custom_table_data_input', 'records', variables.tableId],
      })
    },
  })
}

export function useImportCustomTableRecords() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ tableId, file }: { tableId: number; file: File }) => {
      const token = getToken()
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(`${BASE_URL}/custom_table_data_input/tables/${tableId}/import`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.message ?? '匯入失敗')
      }
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: ['custom_table_data_input', 'records', variables.tableId],
      })
    },
  })
}

export function useCustomTableOptionsQuery() {
  return useQuery<{ id: number; name: string }[]>({
    queryKey: ['custom_table_data_input', 'options'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/custom_table_data_input/options`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return (json.data ?? json) as { id: number; name: string }[]
    },
  })
}

export async function downloadCustomTableFormat(tableId: number) {
  const token = useAuthStore.getState().token
  const res = await fetch(`${BASE_URL}/custom_table_data_input/tables/${tableId}/format`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.message ?? '下載失敗')
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'format.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}
