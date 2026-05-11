// src/pages/fn_ai_partner_chat/FnAiPartnerChatPage.tsx
import { useState } from 'react'
import Box from '@mui/material/Box'
import FnAiPartnerChatList from './FnAiPartnerChatList'
import FnAiPartnerChat from './FnAiPartnerChat'
import type { AiPartner } from '@/queries/useAiPartnerChatQuery'

type View = 'list' | 'chat'

export default function FnAiPartnerChatPage() {
  const [view, setView] = useState<View>('list')
  const [selectedPartner, setSelectedPartner] = useState<AiPartner | null>(null)

  function handleEnterChat(partner: AiPartner) {
    setSelectedPartner(partner)
    setView('chat')
  }

  function handleBack() {
    setView('list')
    setSelectedPartner(null)
  }

  return (
    <Box sx={{ p: '14px 20px', bgcolor: '#f0f4f8', minHeight: '100%' }}>
      {view === 'list' && <FnAiPartnerChatList onEnterChat={handleEnterChat} />}
      {view === 'chat' && selectedPartner && (
        <FnAiPartnerChat partner={selectedPartner} onBack={handleBack} />
      )}
    </Box>
  )
}
