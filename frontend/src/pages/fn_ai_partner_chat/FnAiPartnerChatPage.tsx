// src/pages/fn_ai_partner_chat/FnAiPartnerChatPage.tsx
import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import Box from '@mui/material/Box'
import FnAiPartnerChatList from './FnAiPartnerChatList'
import FnAiPartnerChat from './FnAiPartnerChat'
import { useAiPartnersQuery } from '@/queries/useAiPartnerChatQuery'
import type { AiPartner } from '@/queries/useAiPartnerChatQuery'

type View = 'list' | 'chat'

export default function FnAiPartnerChatPage() {
  const [searchParams] = useSearchParams()
  const [view, setView] = useState<View>('list')
  const [selectedPartner, setSelectedPartner] = useState<AiPartner | null>(null)
  const { data: partners = [] } = useAiPartnersQuery()

  useEffect(() => {
    const partnerId = searchParams.get('partnerId')
    if (!partnerId || partners.length === 0) return
    const partner = partners.find((p) => p.id === Number(partnerId))
    if (partner) {
      setSelectedPartner(partner)
      setView('chat')
    }
  }, [searchParams, partners])

  function handleEnterChat(partner: AiPartner) {
    setSelectedPartner(partner)
    setView('chat')
  }

  function handleBack() {
    setView('list')
    setSelectedPartner(null)
  }

  return (
    <Box sx={{ mt: '-7px' }}>
      {view === 'list' && <FnAiPartnerChatList onEnterChat={handleEnterChat} />}
      {view === 'chat' && selectedPartner && (
        <FnAiPartnerChat partner={selectedPartner} onBack={handleBack} />
      )}
    </Box>
  )
}
