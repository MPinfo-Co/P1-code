// src/queries/useAiPartnerChatQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL

export interface AiPartner {
  id: number
  name: string
  description: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  image_url: string | null
  created_at: string
}

export interface ChatHistory {
  conversation_id: string | null
  messages: ChatMessage[]
  suggestions: string[]
}

export interface NewChatResponse {
  conversation_id: string
  messages: ChatMessage[]
  suggestions: string[]
}

export interface SendMessagePayload {
  partner_id: number
  conversation_id: string
  message?: string
  image?: File | null
}

export interface SendMessageResponse {
  content: string
  suggestions: string[]
}

export interface AiPartnerOption {
  id: number
  name: string
}

function getToken() {
  return useAuthStore.getState().token
}

export function useAiPartnersQuery() {
  return useQuery<AiPartner[]>({
    queryKey: ['aiPartners'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/ai-partner-chat/partners`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('取得 AI 夥伴清單失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useAiPartnerHistoryQuery(partnerId: number | null) {
  return useQuery<ChatHistory>({
    queryKey: ['aiPartnerHistory', partnerId],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/ai-partner-chat/history?partner_id=${partnerId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('取得對話歷史失敗')
      const json = await res.json()
      return json.data ?? json
    },
    enabled: partnerId !== null,
  })
}

export function useNewAiPartnerChat() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (partnerId: number): Promise<NewChatResponse> => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/ai-partner-chat/new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ partner_id: partnerId }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail ?? err.message ?? '建立新對話失敗')
      }
      const json = await res.json()
      return json.data ?? json
    },
    onSuccess: (_data, partnerId) => {
      queryClient.invalidateQueries({ queryKey: ['aiPartnerHistory', partnerId] })
    },
  })
}

export function useSendAiPartnerMessage() {
  return useMutation({
    mutationFn: async (payload: SendMessagePayload): Promise<SendMessageResponse> => {
      const token = getToken()
      const formData = new FormData()
      formData.append('partner_id', String(payload.partner_id))
      formData.append('conversation_id', payload.conversation_id)
      if (payload.message) formData.append('message', payload.message)
      if (payload.image) formData.append('image', payload.image)

      const res = await fetch(`${BASE_URL}/ai-partner-chat/send`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        const err = new Error(body.detail ?? body.message ?? '訊息傳送失敗') as Error & {
          status: number
        }
        err.status = res.status
        throw err
      }
      const json = await res.json()
      return json.data ?? json
    },
  })
}

export function useAiPartnerOptionsQuery() {
  return useQuery<AiPartnerOption[]>({
    queryKey: ['aiPartnerOptions'],
    queryFn: async () => {
      const token = getToken()
      const res = await fetch(`${BASE_URL}/ai-partner-chat/options`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) throw new Error('取得 AI 夥伴選項失敗')
      const json = await res.json()
      return json.data ?? json
    },
  })
}
