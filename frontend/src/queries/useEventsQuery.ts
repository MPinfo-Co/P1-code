// src/queries/useEventsQuery.ts
import { useQuery } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

function getToken() {
  return useAuthStore.getState().token
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

export function useEventsQuery(params: EventsQueryParams = {}) {
  const { page = 1, pageSize = 10, status, dateStart, dateEnd, keyword } = params
  return useQuery<PaginatedEventsResponse>({
    queryKey: ['events', { page, pageSize, status, dateStart, dateEnd, keyword }],
    queryFn: async () => {
      const token = getToken()
      const search = new URLSearchParams()
      search.set('page', String(page))
      search.set('page_size', String(pageSize))
      if (status && status !== 'all') search.set('status', status)
      if (dateStart) search.set('date_from', dateStart)
      if (dateEnd) search.set('date_to', dateEnd)
      if (keyword) search.set('keyword', keyword)
      const res = await fetch(`${BASE_URL}/events?${search.toString()}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
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
