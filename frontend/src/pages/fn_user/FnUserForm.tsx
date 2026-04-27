import { useState } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Checkbox from '@mui/material/Checkbox'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import FormControlLabel from '@mui/material/FormControlLabel'
import FormHelperText from '@mui/material/FormHelperText'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import type { UserRow } from '@/queries/useUsersQuery'
import {
  useRolesOptionsQuery,
  useCreateUser,
  useUpdateUser,
} from '@/queries/useUsersQuery'

// ── Props ─────────────────────────────────────────────────────────

interface Props {
  open: boolean
  /** undefined = 新增模式；有值 = 修改模式 */
  user?: UserRow | null
  onClose: () => void
  onSuccess: () => void
}

// ── Form state type ───────────────────────────────────────────────

interface FormState {
  name: string
  email: string
  password: string
  roleIds: number[]
}

function emptyForm(): FormState {
  return { name: '', email: '', password: '', roleIds: [] }
}

// ── Validation ────────────────────────────────────────────────────

interface FormErrors {
  name?: string
  email?: string
  password?: string
  roleIds?: string
}

function validate(form: FormState, isEdit: boolean): FormErrors {
  const errors: FormErrors = {}

  if (!form.name.trim()) {
    errors.name = '名稱不可空白'
  } else if (form.name.length > 100) {
    errors.name = '名稱不可超過 100 字'
  }

  if (!isEdit) {
    // Email 在修改模式為唯讀，不驗證
    if (!form.email.trim()) {
      errors.email = 'Email 不可空白'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      errors.email = 'Email 格式不正確'
    }
  }

  if (!form.password) {
    errors.password = '密碼不可空白'
  } else if (form.password.length < 8) {
    errors.password = '密碼至少需要 8 個字元'
  }

  if (form.roleIds.length === 0) {
    errors.roleIds = '至少需要選擇一個角色'
  }

  return errors
}

// ── Component ─────────────────────────────────────────────────────

function initForm(user?: UserRow | null): FormState {
  if (user) {
    return {
      name: user.name,
      email: user.email,
      password: '',
      roleIds: user.roles.map((r) => r.id),
    }
  }
  return emptyForm()
}

export default function FnUserForm({ open, user, onClose, onSuccess }: Props) {
  const isEdit = !!user

  const { data: roleOptions = [], isLoading: isRolesLoading } = useRolesOptionsQuery()
  const createUser = useCreateUser()
  const updateUser = useUpdateUser()

  const [form, setForm] = useState<FormState>(() => initForm(user))
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)

  function handleToggleRole(id: number) {
    setForm((prev) => ({
      ...prev,
      roleIds: prev.roleIds.includes(id)
        ? prev.roleIds.filter((x) => x !== id)
        : [...prev.roleIds, id],
    }))
  }

  function handleToggleAll() {
    const allIds = roleOptions.map((r) => r.id)
    const isAllSelected = allIds.every((id) => form.roleIds.includes(id))
    setForm((prev) => ({ ...prev, roleIds: isAllSelected ? [] : allIds }))
  }

  async function handleSave() {
    const errs = validate(form, isEdit)
    if (Object.keys(errs).length > 0) {
      setErrors(errs)
      return
    }
    setErrors({})
    setSubmitError(null)

    try {
      if (isEdit && user) {
        await updateUser.mutateAsync({
          email: user.email,
          payload: {
            name: form.name,
            password: form.password || undefined,
            role_ids: form.roleIds,
          },
        })
      } else {
        await createUser.mutateAsync({
          name: form.name,
          email: form.email,
          password: form.password,
          role_ids: form.roleIds,
        })
      }
      onSuccess()
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : '操作失敗，請稍後再試')
    }
  }

  const isMutating = createUser.isPending || updateUser.isPending
  const isAllSelected =
    roleOptions.length > 0 && roleOptions.every((r) => form.roleIds.includes(r.id))

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ fontWeight: 800 }}>{isEdit ? '修改帳號' : '新增帳號'}</DialogTitle>

      <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}>
        {submitError && (
          <Alert severity="error" sx={{ fontSize: 13 }}>
            {submitError}
          </Alert>
        )}

        {/* 名稱 */}
        <TextField
          label="名稱"
          value={form.name}
          onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
          fullWidth
          size="small"
          error={!!errors.name}
          helperText={errors.name}
          inputProps={{ maxLength: 100 }}
        />

        {/* Email */}
        <TextField
          label="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
          fullWidth
          size="small"
          error={!!errors.email}
          helperText={errors.email}
          InputProps={{ readOnly: isEdit }}
          sx={isEdit ? { '& .MuiInputBase-root': { bgcolor: '#f8fafc' } } : undefined}
        />

        {/* 密碼 */}
        <TextField
          label="密碼"
          type="password"
          value={form.password}
          onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
          fullWidth
          size="small"
          error={!!errors.password}
          helperText={errors.password}
        />

        {/* 角色 */}
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
              角色
            </Typography>
            <Button
              size="small"
              onClick={handleToggleAll}
              disabled={isRolesLoading}
              sx={{ fontSize: 12 }}
            >
              {isAllSelected ? '取消全選' : '全選'}
            </Button>
          </Box>

          <Box
            sx={{
              border: `1px solid ${errors.roleIds ? '#d32f2f' : '#e2e8f0'}`,
              borderRadius: 1,
              p: 1,
              bgcolor: '#f8fafc',
              maxHeight: 180,
              overflowY: 'auto',
            }}
          >
            {isRolesLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                <CircularProgress size={20} />
              </Box>
            ) : (
              roleOptions.map((role) => (
                <FormControlLabel
                  key={role.id}
                  control={
                    <Checkbox
                      size="small"
                      checked={form.roleIds.includes(role.id)}
                      onChange={() => handleToggleRole(role.id)}
                      sx={{ color: '#2e3f6e', '&.Mui-checked': { color: '#2e3f6e' } }}
                    />
                  }
                  label={<Typography sx={{ fontSize: 13 }}>{role.name}</Typography>}
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

          {errors.roleIds && (
            <FormHelperText error sx={{ ml: 1.5 }}>
              {errors.roleIds}
            </FormHelperText>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} sx={{ color: '#64748b' }} disabled={isMutating}>
          取消
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={isMutating}
          sx={{ bgcolor: '#2e3f6e', '&:hover': { bgcolor: '#1e2d52' } }}
        >
          {isMutating ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
