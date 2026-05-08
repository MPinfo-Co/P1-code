// src/queries/useCompanyDataQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface CompanyDataRow {
  id: number
  name: string
  content: string
}

export interface QueryParams {
  keyword?: string
}

export interface CreateCompanyDataPayload {
  name: string
  content: string
}

export interface UpdateCompanyDataPayload {
  name: string
  content: string
}

function getToken() {
  return useAuthStore.getState().token
}

export function useCompanyDataQuery(params: QueryParams = {}) {
  return useQuery<CompanyDataRow[]>({
    queryKey: ['company-data', params],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      if (params.keyword) search.set('keyword', params.keyword)
      const qs = search.toString()
      const res = await fetch(`${BASE_URL}/company-data${qs ? `?${qs}` : ''}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('查詢失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useCreateCompanyData() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: CreateCompanyDataPayload) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/company-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: payload.name,
          content: payload.content,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? '新增失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company-data'] })
    },
  })
}

export function useUpdateCompanyData() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: UpdateCompanyDataPayload }) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/company-data/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: payload.name,
          content: payload.content,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? '更新失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company-data'] })
    },
  })
}

export function useDeleteCompanyData() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/company-data/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? '刪除失敗')
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company-data'] })
    },
  })
}
