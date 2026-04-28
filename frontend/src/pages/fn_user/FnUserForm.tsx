// src/pages/fn_user/FnUserForm.tsx
import { useState } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Checkbox from '@mui/material/Checkbox'
import FormControlLabel from '@mui/material/FormControlLabel'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import { useRoleOptionsQuery } from '@/queries/useRoleOptionsQuery'
import { useCreateUser, useUpdateUser } from '@/queries/useUsersQuery'
import type { UserRow } from '@/queries/useUsersQuery'

interface Props {
  open: boolean
  row: UserRow | null
  onClose: () => void
  onSuccess: () => void
}

interface FormErrors {
  name?: string
  email?: string
  password?: string
  roles?: string
}

export default function FnUserForm({ open, row, onClose, onSuccess }: Props) {
  const isEdit = row !== null

  const [name, setName] = useState(() => row?.name ?? '')
  const [email, setEmail] = useState(() => row?.email ?? '')
  const [password, setPassword] = useState('')
  const [selectedRoleIds, setSelectedRoleIds] = useState<number[]>(
    () => row?.roles.map((r) => r.id) ?? []
  )
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)

  const { data: roleOptions = [], isLoading: isRolesLoading } = useRoleOptionsQuery()
  const createUser = useCreateUser()
  const updateUser = useUpdateUser()

  function validate(): boolean {
    const newErrors: FormErrors = {}
    if (!name.trim()) newErrors.name = '名稱不可空白'
    else if (name.trim().length > 100) newErrors.name = '名稱最長 100 字'
    if (!email.trim()) newErrors.email = 'Email 不可空白'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) newErrors.email = 'Email 格式不正確'
    if (!isEdit || password) {
      if (!password) newErrors.password = '密碼不可空白'
      else if (password.length < 8) newErrors.password = '密碼最少 8 字元'
    }
    if (selectedRoleIds.length === 0) newErrors.roles = '至少選擇一個角色'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  function handleToggleRole(id: number) {
    setSelectedRoleIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  function handleToggleAll() {
    const allIds = roleOptions.map((r) => r.id)
    const isAllSelected = allIds.every((id) => selectedRoleIds.includes(id))
    setSelectedRoleIds(isAllSelected ? [] : allIds)
  }

  async function handleSave() {
    if (!validate()) return
    setSubmitError(null)
    try {
      if (isEdit) {
        const payload: { name?: string; password?: string; role_ids?: number[] } = {
          name: name.trim(),
          role_ids: selectedRoleIds,
        }
        if (password) payload.password = password
        await updateUser.mutateAsync({ email: row!.email, payload })
      } else {
        await createUser.mutateAsync({
          name: name.trim(),
          email: email.trim(),
          password,
          role_ids: selectedRoleIds,
        })
      }
      onSuccess()
      onClose()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : '操作失敗，請稍後再試')
    }
  }

  const isSubmitting = createUser.isPending || updateUser.isPending

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ fontWeight: 800 }}>{isEdit ? '修改帳號' : '新增帳號'}</DialogTitle>
      <DialogContent
        sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}
      >
        {submitError && (
          <Alert severity="error" sx={{ mb: 0 }}>
            {submitError}
          </Alert>
        )}
        <TextField
          label="名稱"
          value={name}
          onChange={(e) => setName(e.target.value)}
          fullWidth
          size="small"
          error={!!errors.name}
          helperText={errors.name}
        />
        <TextField
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          fullWidth
          size="small"
          error={!!errors.email}
          helperText={errors.email}
          disabled={isEdit}
          InputProps={isEdit ? { readOnly: true } : undefined}
        />
        <TextField
          label="密碼"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          fullWidth
          size="small"
          error={!!errors.password}
          helperText={errors.password ?? (isEdit ? '不修改請留空' : undefined)}
        />
        <Box>
          <Box
            sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}
          >
            <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>角色</Typography>
            <Button size="small" onClick={handleToggleAll} sx={{ fontSize: 12 }}>
              全選
            </Button>
          </Box>
          {errors.roles && (
            <Typography sx={{ fontSize: 12, color: 'error.main', mb: 0.5 }}>
              {errors.roles}
            </Typography>
          )}
          <Box
            sx={{
              border: `1px solid ${errors.roles ? '#d32f2f' : '#e2e8f0'}`,
              borderRadius: 1,
              p: 1,
              bgcolor: '#f8fafc',
            }}
          >
            {isRolesLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 1 }}>
                <CircularProgress size={20} />
              </Box>
            ) : (
              roleOptions.map((r) => (
                <FormControlLabel
                  key={r.id}
                  control={
                    <Checkbox
                      size="small"
                      checked={selectedRoleIds.includes(r.id)}
                      onChange={() => handleToggleRole(r.id)}
                      sx={{ color: '#2e3f6e', '&.Mui-checked': { color: '#2e3f6e' } }}
                    />
                  }
                  label={<Typography sx={{ fontSize: 13 }}>{r.name}</Typography>}
                  sx={{
                    display: 'flex',
                    mb: 0.5,
                    bgcolor: 'white',
                    borderRadius: 1,
                    border: '1px solid #e2e8f0',
                    px: 1,
                    mx: 0,
                  }}
                />
              ))
            )}
          </Box>
        </Box>
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
