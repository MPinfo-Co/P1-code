// src/pages/fn_company_data/FnCompanyDataForm.tsx
import { useState } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import { useCreateCompanyData, useUpdateCompanyData } from '@/queries/useCompanyDataQuery'
import type { CompanyDataRow } from '@/queries/useCompanyDataQuery'

interface Props {
  open: boolean
  row: CompanyDataRow | null
  onClose: () => void
  onSuccess: () => void
}

interface FormErrors {
  name?: string
  content?: string
}

export default function FnCompanyDataForm({ open, row, onClose, onSuccess }: Props) {
  const isEdit = row !== null

  const [name, setName] = useState(() => row?.name ?? '')
  const [content, setContent] = useState(() => row?.content ?? '')
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)

  const createCompanyData = useCreateCompanyData()
  const updateCompanyData = useUpdateCompanyData()

  function validate(): boolean {
    const newErrors: FormErrors = {}
    if (!name.trim()) newErrors.name = '資料名稱不可空白'
    else if (name.trim().length > 200) newErrors.name = '資料名稱不可超過 200 字'
    const nonEmptyLines = content.split('\n').filter((line) => line.trim() !== '')
    if (nonEmptyLines.length === 0) newErrors.content = '內容不可空白'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  async function handleSave() {
    if (!validate()) return
    setSubmitError(null)
    try {
      if (isEdit) {
        await updateCompanyData.mutateAsync({
          id: row!.id,
          payload: {
            name: name.trim(),
            content: content.trim(),
          },
        })
      } else {
        await createCompanyData.mutateAsync({
          name: name.trim(),
          content: content.trim(),
        })
      }
      onSuccess()
      onClose()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : '操作失敗，請稍後再試')
    }
  }

  const isSubmitting = createCompanyData.isPending || updateCompanyData.isPending

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontSize: 16, fontWeight: 600 }}>
        {isEdit ? '編輯資料' : '新增資料'}
      </DialogTitle>
      <DialogContent
        sx={{ pt: '16px !important', display: 'flex', flexDirection: 'column', gap: 2 }}
      >
        {submitError && (
          <Alert severity="error" sx={{ mb: 0 }}>
            {submitError}
          </Alert>
        )}
        <TextField
          label="資料名稱"
          value={name}
          onChange={(e) => setName(e.target.value)}
          fullWidth
          size="small"
          error={!!errors.name}
          helperText={errors.name}
          inputProps={{ maxLength: 200 }}
        />
        <TextField
          label="內容"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          fullWidth
          size="small"
          multiline
          minRows={4}
          error={!!errors.content}
          helperText={errors.content}
        />
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={isSubmitting}>
          取消
        </Button>
        <Button onClick={handleSave} variant="contained" disabled={isSubmitting}>
          {isSubmitting ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
