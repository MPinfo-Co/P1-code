// src/pages/fn_dept/FnDeptForm.tsx
import { useState } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import { useDeptOptionsQuery, useCreateDept, useUpdateDept } from '@/queries/useDeptQuery'
import type { DeptRow } from '@/queries/useDeptQuery'

interface Props {
  open: boolean
  row: DeptRow | null
  onClose: () => void
  onSuccess: () => void
}

interface FormErrors {
  name?: string
  code?: string
}

export default function FnDeptForm({ open, row, onClose, onSuccess }: Props) {
  const isEdit = row !== null

  const [name, setName] = useState(() => row?.name ?? '')
  const [code, setCode] = useState(() => row?.code ?? '')
  const [parentId, setParentId] = useState<number | ''>(() => {
    // We don't have parent_id on DeptRow directly, only parent_name
    return ''
  })
  const [headName, setHeadName] = useState(() => row?.head_name ?? '')
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)

  const { data: deptOptions = [] } = useDeptOptionsQuery()
  const createDept = useCreateDept()
  const updateDept = useUpdateDept()

  function validate(): boolean {
    const newErrors: FormErrors = {}
    if (!name.trim()) newErrors.name = '部門名稱不可空白'
    else if (name.trim().length > 100) newErrors.name = '部門名稱最長 100 字'
    if (!code.trim()) newErrors.code = '部門代碼不可空白'
    else if (code.trim().length > 50) newErrors.code = '部門代碼最長 50 字'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  async function handleSave() {
    if (!validate()) return
    setSubmitError(null)
    try {
      if (isEdit) {
        await updateDept.mutateAsync({
          id: row!.id,
          payload: {
            name: name.trim(),
            code: code.trim(),
            parent_id: parentId !== '' ? parentId : null,
            head_name: headName.trim() || undefined,
          },
        })
      } else {
        await createDept.mutateAsync({
          name: name.trim(),
          code: code.trim(),
          parent_id: parentId !== '' ? parentId : null,
          head_name: headName.trim() || undefined,
        })
      }
      onSuccess()
      onClose()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : '操作失敗，請稍後再試')
    }
  }

  const isSubmitting = createDept.isPending || updateDept.isPending

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ fontWeight: 800 }}>{isEdit ? '編輯部門' : '新增部門'}</DialogTitle>
      <DialogContent
        sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}
      >
        {submitError && (
          <Alert severity="error" sx={{ mb: 0 }}>
            {submitError}
          </Alert>
        )}
        <TextField
          label="部門名稱"
          value={name}
          onChange={(e) => setName(e.target.value)}
          fullWidth
          size="small"
          error={!!errors.name}
          helperText={errors.name}
        />
        <TextField
          label="部門代碼"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          fullWidth
          size="small"
          error={!!errors.code}
          helperText={errors.code}
        />
        <Box>
          <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b', mb: 0.5 }}>
            上級部門
          </Typography>
          <Select
            value={parentId}
            onChange={(e) => setParentId(e.target.value as number | '')}
            size="small"
            displayEmpty
            fullWidth
            sx={{ fontSize: 13 }}
          >
            <MenuItem value="">（無，頂層部門）</MenuItem>
            {deptOptions.map((d) => (
              <MenuItem key={d.id} value={d.id}>
                {d.name}
              </MenuItem>
            ))}
          </Select>
        </Box>
        <TextField
          label="負責人"
          value={headName}
          onChange={(e) => setHeadName(e.target.value)}
          fullWidth
          size="small"
          placeholder="選填"
        />
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} sx={{ color: '#64748b' }} disabled={isSubmitting}>
          取消
        </Button>
        <Button onClick={handleSave} variant="contained" disabled={isSubmitting}>
          {isSubmitting ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
