// src/queries/useEventsQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

function getToken() {
  return useAuthStore.getState().token
}

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export interface EventRow {
  id: number | string
  title: string
  star_rank: number
  event_date: string
  date_end?: string
  detection_count?: number
  affected_summary: string
  affected_detail?: string
  current_status: string
  assignee_user_id?: number | null
}

export interface PaginatedEventsResponse {
  items: EventRow[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface EventsQueryParams {
  page?: number
  pageSize?: number
  status?: string
  dateStart?: string
  dateEnd?: string
  keyword?: string
}

export interface LogObject {
  id?: number | string
  timestamp?: number
  host?: string
  program?: string
  message: string
}

export interface EventDetail {
  id: number
  event_date: string
  date_end?: string | null
  star_rank: number
  title: string
  description?: string | null
  affected_summary: string
  affected_detail?: string | null
  current_status: string
  match_key: string
  detection_count: number
  continued_from?: number | null
  assignee_user_id?: number | null
  suggests?: string[] | null
  logs?: (string | LogObject)[] | null
  ioc_list?: unknown[] | null
  mitre_tags?: string[] | null
  created_at: string
  updated_at: string
}

export interface EventHistoryEntry {
  id: number
  event_id: number
  user_id: number
  action: string
  old_status?: string | null
  new_status?: string | null
  note?: string | null
  resolved_at?: string | null
  created_at: string
}

export interface UpdateEventPayload {
  current_status?: string
  assignee_user_id?: number | null
}

export interface AddEventHistoryPayload {
  action: string
  old_status?: string | null
  new_status?: string | null
  note?: string | null
  resolved_at?: string | null
}

export function useEventsQuery(params: EventsQueryParams = {}) {
  const { page = 1, pageSize = 10, status, dateStart, dateEnd, keyword } = params
  return useQuery<PaginatedEventsResponse>({
    queryKey: ['events', { page, pageSize, status, dateStart, dateEnd, keyword }],
    queryFn: async () => {
      const search = new URLSearchParams()
      search.set('page', String(page))
      search.set('page_size', String(pageSize))
      if (status && status !== 'all') search.set('status', status)
      if (dateStart) search.set('date_from', dateStart)
      if (dateEnd) search.set('date_to', dateEnd)
      if (keyword) search.set('keyword', keyword)
      const res = await fetch(`${BASE_URL}/events?${search.toString()}`, {
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      if (json.items !== undefined) {
        return json as PaginatedEventsResponse
      }
      // Legacy fallback
      const items: EventRow[] = Array.isArray(json) ? json : []
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

export function useEventDetailQuery(eventId: string | number | undefined) {
  return useQuery<EventDetail>({
    queryKey: ['event', eventId],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/events/${eventId}`, {
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      return res.json()
    },
    enabled: eventId !== undefined && eventId !== '',
  })
}

export function useEventHistoryQuery(eventId: string | number | undefined) {
  return useQuery<EventHistoryEntry[]>({
    queryKey: ['event-history', eventId],
    queryFn: async () => {
      const res = await fetch(`${BASE_URL}/events/${eventId}/history`, {
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      return json.items ?? []
    },
    enabled: eventId !== undefined && eventId !== '',
  })
}

export function useUpdateEvent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string | number; payload: UpdateEventPayload }) => {
      const res = await fetch(`${BASE_URL}/events/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '更新失敗')
      }
      return (await res.json()) as EventDetail
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['event', id] })
      queryClient.invalidateQueries({ queryKey: ['events'] })
    },
  })
}

export function useAddEventHistory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      id,
      payload,
    }: {
      id: string | number
      payload: AddEventHistoryPayload
    }) => {
      const res = await fetch(`${BASE_URL}/events/${id}/history`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '新增失敗')
      }
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['event-history', id] })
      queryClient.invalidateQueries({ queryKey: ['event', id] })
    },
  })
}
