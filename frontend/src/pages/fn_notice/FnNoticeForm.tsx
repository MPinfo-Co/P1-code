// src/pages/fn_notice/FnNoticeForm.tsx
import { useState } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import { useCreateNotice } from '@/queries/useNoticesQuery'

interface Props {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

interface FormErrors {
  title?: string
  content?: string
  expires_at?: string
}

export default function FnNoticeForm({ open, onClose, onSuccess }: Props) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [expiresAt, setExpiresAt] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)

  const createNotice = useCreateNotice()

  function validate(): boolean {
    const newErrors: FormErrors = {}
    if (!title.trim()) newErrors.title = '標題不可為空'
    if (!content.trim()) newErrors.content = '內容不可為空'
    if (!expiresAt) {
      newErrors.expires_at = '有效期限不可為空'
    } else {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const selected = new Date(expiresAt)
      if (selected < today) newErrors.expires_at = '有效期限須為今日或未來日期'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  function handleClose() {
    setTitle('')
    setContent('')
    setExpiresAt('')
    setErrors({})
    setSubmitError(null)
    onClose()
  }

  async function handleSave() {
    if (!validate()) return
    setSubmitError(null)
    try {
      await createNotice.mutateAsync({
        title: title.trim(),
        content: content.trim(),
        expires_at: expiresAt,
      })
      handleClose()
      onSuccess()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : '新增失敗，請稍後再試')
    }
  }

  const isSubmitting = createNotice.isPending

  // Compute today's date string (YYYY-MM-DD) for min date
  const todayStr = new Date().toISOString().split('T')[0]

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ fontWeight: 800 }}>新增公告</DialogTitle>
      <DialogContent
        sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}
      >
        {submitError && (
          <Alert severity="error" sx={{ mb: 0 }}>
            {submitError}
          </Alert>
        )}
        <TextField
          label="標題"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          fullWidth
          size="small"
          error={!!errors.title}
          helperText={errors.title}
        />
        <TextField
          label="內容"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          fullWidth
          size="small"
          multiline
          minRows={3}
          error={!!errors.content}
          helperText={errors.content}
        />
        <TextField
          label="有效期限"
          type="date"
          value={expiresAt}
          onChange={(e) => setExpiresAt(e.target.value)}
          fullWidth
          size="small"
          inputProps={{ min: todayStr }}
          InputLabelProps={{ shrink: true }}
          error={!!errors.expires_at}
          helperText={errors.expires_at}
        />
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose} sx={{ color: '#64748b' }} disabled={isSubmitting}>
          取消
        </Button>
        <Button onClick={handleSave} variant="contained" disabled={isSubmitting}>
          {isSubmitting ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
