// src/pages/fn_ai_partner_chat/FnAiPartnerChat.tsx
import React, { useState, useEffect, useRef } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import TextField from '@mui/material/TextField'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import SendIcon from '@mui/icons-material/Send'
import ImageIcon from '@mui/icons-material/Image'
import CloseIcon from '@mui/icons-material/Close'
import {
  useAiPartnerHistoryQuery,
  useNewAiPartnerChat,
  useSendAiPartnerMessage,
} from '@/queries/useAiPartnerChatQuery'
import type { AiPartner, ChatMessage } from '@/queries/useAiPartnerChatQuery'

interface Props {
  partner: AiPartner
  onBack: () => void
}

export default function FnAiPartnerChat({ partner, onBack }: Props) {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [inputText, setInputText] = useState('')
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  const [isConfirmNewOpen, setIsConfirmNewOpen] = useState(false)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: historyData, isLoading: isHistoryLoading } = useAiPartnerHistoryQuery(partner.id)
  const newChat = useNewAiPartnerChat()
  const sendMessage = useSendAiPartnerMessage()

  // Initialize chat on history load
  useEffect(() => {
    if (!historyData || isInitialized) return
    if (historyData.conversation_id) {
      setConversationId(historyData.conversation_id)
      setMessages(historyData.messages)
      setSuggestions(historyData.suggestions)
      setIsInitialized(true)
    } else {
      // No existing conversation — start new one
      newChat.mutate(partner.id, {
        onSuccess: (data) => {
          setConversationId(data.conversation_id)
          setMessages(data.messages)
          setSuggestions(data.suggestions)
          setIsInitialized(true)
        },
      })
    }
  }, [historyData, isInitialized, partner.id]) // eslint-disable-line react-hooks/exhaustive-deps

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isSending])

  function handleImageSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null
    if (!file) return
    setSelectedImage(file)
    setImagePreviewUrl(URL.createObjectURL(file))
  }

  function handleRemoveImage() {
    setSelectedImage(null)
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl)
    setImagePreviewUrl(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function handleChipClick(text: string) {
    setInputText(text)
  }

  async function handleSend() {
    if (!inputText.trim() && !selectedImage) return
    if (!conversationId) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: inputText,
      image_url: imagePreviewUrl,
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setSuggestions([])
    const textToSend = inputText
    const imageToSend = selectedImage
    setInputText('')
    setSelectedImage(null)
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl)
    setImagePreviewUrl(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    setIsSending(true)
    setSendError(null)

    sendMessage.mutate(
      {
        partner_id: partner.id,
        conversation_id: conversationId,
        message: textToSend || undefined,
        image: imageToSend,
      },
      {
        onSuccess: (data) => {
          const aiMessage: ChatMessage = {
            role: 'assistant',
            content: data.content,
            image_url: null,
            created_at: new Date().toISOString(),
          }
          setMessages((prev) => [...prev, aiMessage])
          setSuggestions(data.suggestions)
          setIsSending(false)
        },
        onError: (err) => {
          const msg = err instanceof Error ? err.message : 'AI 服務暫時無法使用，請稍後再試'
          setSendError(
            msg.includes('503') || msg.includes('無法使用')
              ? 'AI 服務暫時無法使用，請稍後再試'
              : msg
          )
          setIsSending(false)
        },
      }
    )
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleBack() {
    handleRemoveImage()
    onBack()
  }

  function handleConfirmNewChat() {
    setIsConfirmNewOpen(false)
    newChat.mutate(partner.id, {
      onSuccess: (data) => {
        setConversationId(data.conversation_id)
        setMessages(data.messages)
        setSuggestions(data.suggestions)
        setInputText('')
        handleRemoveImage()
        setSendError(null)
      },
    })
  }

  const isLoading = isHistoryLoading || newChat.isPending

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 40px - 28px)' }}>
      {/* Top bar */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          pb: 1.25,
          flexShrink: 0,
          gap: 1,
        }}
      >
        <Typography sx={{ fontSize: 15, fontWeight: 700, color: '#1e293b', flex: 1 }}>
          {partner.name}
        </Typography>
        <Button
          size="small"
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={handleBack}
          sx={{
            fontSize: 12,
            height: 28,
            borderRadius: '3px',
            borderColor: '#cbd5e1',
            color: '#475569',
            '&:hover': { bgcolor: '#f1f5f9' },
          }}
        >
          返回
        </Button>
        <Button
          size="small"
          variant="outlined"
          onClick={() => setIsConfirmNewOpen(true)}
          sx={{
            fontSize: 12,
            height: 28,
            borderRadius: '3px',
            borderColor: '#6366f1',
            color: '#6366f1',
            '&:hover': { bgcolor: '#f0f0ff' },
          }}
        >
          開始新對話
        </Button>
      </Box>

      {/* Messages area */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 1.5,
          py: 1,
          px: 0.5,
        }}
      >
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress size={32} />
          </Box>
        )}

        {messages.map((msg, idx) => (
          <Box
            key={idx}
            sx={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <Box
              sx={{
                maxWidth: '72%',
                bgcolor: msg.role === 'user' ? '#6366f1' : '#f1f5f9',
                color: msg.role === 'user' ? 'white' : '#1e293b',
                px: 2,
                py: 1.25,
                borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                fontSize: 14,
                lineHeight: 1.6,
              }}
            >
              {msg.image_url && (
                <Box
                  component="img"
                  src={msg.image_url}
                  sx={{
                    width: 120,
                    height: 120,
                    objectFit: 'cover',
                    borderRadius: 1,
                    mb: 0.75,
                    display: 'block',
                  }}
                />
              )}
              <Typography sx={{ fontSize: 14, whiteSpace: 'pre-wrap', color: 'inherit' }}>
                {msg.content}
              </Typography>
            </Box>
          </Box>
        ))}

        {/* AI loading indicator */}
        {isSending && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
            <Box
              sx={{
                bgcolor: '#f1f5f9',
                px: 2,
                py: 1.25,
                borderRadius: '16px 16px 16px 4px',
                display: 'flex',
                alignItems: 'center',
                gap: 0.75,
              }}
            >
              {[0, 1, 2].map((i) => (
                <Box
                  key={i}
                  sx={{
                    width: 8,
                    height: 8,
                    bgcolor: '#6366f1',
                    borderRadius: '50%',
                    animation: 'aiPulse 1.2s infinite',
                    animationDelay: `${i * 0.2}s`,
                    '@keyframes aiPulse': {
                      '0%, 100%': { opacity: 0.3, transform: 'scale(0.8)' },
                      '50%': { opacity: 1, transform: 'scale(1)' },
                    },
                  }}
                />
              ))}
            </Box>
          </Box>
        )}

        {sendError && (
          <Alert severity="error" sx={{ mx: 0 }}>
            {sendError}
          </Alert>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Suggestions */}
      {suggestions.length > 0 && !isSending && (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.75, py: 1, flexShrink: 0 }}>
          {suggestions.map((s, idx) => (
            <Chip
              key={idx}
              label={s}
              size="small"
              onClick={() => handleChipClick(s)}
              sx={{
                fontSize: 12,
                bgcolor: '#f0f0ff',
                color: '#4f46e5',
                border: '1px solid #c7d2fe',
                cursor: 'pointer',
                '&:hover': { bgcolor: '#e0e7ff' },
              }}
            />
          ))}
        </Box>
      )}

      {/* Input area */}
      <Box sx={{ flexShrink: 0, display: 'flex', alignItems: 'flex-end', gap: 1, pt: 0.5 }}>
        <IconButton
          size="small"
          onClick={() => fileInputRef.current?.click()}
          sx={{ color: '#94a3b8', '&:hover': { color: '#6366f1', bgcolor: '#f0f0ff' } }}
        >
          <ImageIcon fontSize="small" />
        </IconButton>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={handleImageSelect}
        />

        <Box
          sx={{
            flex: 1,
            border: '1px solid #cbd5e1',
            borderRadius: '20px',
            bgcolor: 'white',
            overflow: 'hidden',
            '&:focus-within': { borderColor: '#6366f1' },
          }}
        >
          {imagePreviewUrl && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 1.5, pt: 1 }}>
              <Box
                component="img"
                src={imagePreviewUrl}
                sx={{
                  width: 56,
                  height: 56,
                  objectFit: 'cover',
                  borderRadius: 1,
                  border: '1px solid #e2e8f0',
                }}
              />
              <IconButton
                size="small"
                onClick={handleRemoveImage}
                sx={{
                  bgcolor: '#94a3b8',
                  color: 'white',
                  width: 18,
                  height: 18,
                  '&:hover': { bgcolor: '#64748b' },
                }}
              >
                <CloseIcon sx={{ fontSize: 12 }} />
              </IconButton>
            </Box>
          )}
          <TextField
            multiline
            maxRows={4}
            fullWidth
            placeholder="輸入訊息…"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSending || !isInitialized}
            variant="standard"
            InputProps={{ disableUnderline: true }}
            sx={{
              '& .MuiInputBase-root': { px: 1.5, py: 1, fontSize: 14 },
            }}
          />
        </Box>

        <IconButton
          onClick={handleSend}
          disabled={(!inputText.trim() && !selectedImage) || isSending || !isInitialized}
          sx={{
            bgcolor: '#6366f1',
            color: 'white',
            width: 36,
            height: 36,
            '&:hover': { bgcolor: '#4f46e5' },
            '&.Mui-disabled': { bgcolor: '#e2e8f0', color: '#94a3b8' },
          }}
        >
          <SendIcon fontSize="small" />
        </IconButton>
      </Box>

      {/* Confirm new chat dialog */}
      <Dialog
        open={isConfirmNewOpen}
        onClose={() => setIsConfirmNewOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 700, fontSize: 16 }}>開始新對話</DialogTitle>
        <DialogContent>
          <Typography sx={{ fontSize: 14 }}>確定要清除目前對話並重新開始嗎？</Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setIsConfirmNewOpen(false)} sx={{ color: '#64748b' }}>
            取消
          </Button>
          <Button
            onClick={handleConfirmNewChat}
            variant="contained"
            sx={{ bgcolor: '#6366f1', '&:hover': { bgcolor: '#4f46e5' } }}
          >
            確認
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
