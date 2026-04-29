// src/pages/fn_role/FnRoleForm.tsx
import { useState, useEffect } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import type { RoleRow } from '@/queries/useRolesQuery'
import { useCreateRole, useUpdateRole } from '@/queries/useRolesQuery'
import { useUserOptionsQuery } from '@/queries/useUserOptionsQuery'
import { useFunctionOptionsQuery } from '@/queries/useFunctionOptionsQuery'

interface Props {
  open: boolean
  row: RoleRow | null
  onClose: () => void
  onSuccess: () => void
}

export default function FnRoleForm({ open, row, onClose, onSuccess }: Props) {
  const isEdit = row !== null

  const [roleName, setRoleName] = useState('')
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([])
  const [selectedFunctionIds, setSelectedFunctionIds] = useState<number[]>([])
  const [formError, setFormError] = useState<string | null>(null)

  const { data: userOptions = [] } = useUserOptionsQuery()
  const { data: functionOptions = [] } = useFunctionOptionsQuery()

  const createRole = useCreateRole()
  const updateRole = useUpdateRole()

  const isPending = createRole.isPending || updateRole.isPending

  useEffect(() => {
    if (open) {
      if (row) {
        setRoleName(row.name)
        setSelectedUserIds(row.users.map((u) => u.id))
        setSelectedFunctionIds(row.functions.map((f) => f.function_id))
      } else {
        setRoleName('')
        setSelectedUserIds([])
        setSelectedFunctionIds([])
      }
      setFormError(null)
    }
  }, [open, row])

  function handleToggleUser(id: number) {
    setSelectedUserIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  function handleToggleAllUsers() {
    const allIds = userOptions.map((u) => u.id)
    const isAllSelected = allIds.every((id) => selectedUserIds.includes(id))
    setSelectedUserIds(isAllSelected ? [] : allIds)
  }

  function handleToggleFunction(id: number) {
    setSelectedFunctionIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  async function handleSave() {
    setFormError(null)
    if (!roleName.trim()) {
      setFormError('角色名稱未填寫')
      return
    }
    try {
      if (isEdit && row) {
        await updateRole.mutateAsync({
          name: row.name,
          payload: {
            name: roleName.trim(),
            user_ids: selectedUserIds,
            function_ids: selectedFunctionIds,
          },
        })
      } else {
        await createRole.mutateAsync({
          name: roleName.trim(),
          user_ids: selectedUserIds,
          function_ids: selectedFunctionIds,
        })
      }
      onSuccess()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '操作失敗，請稍後再試')
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontWeight: 800 }}>{isEdit ? '編輯角色' : '新增角色'}</DialogTitle>
      <DialogContent sx={{ pt: '16px !important' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          {formError && (
            <Alert severity="error" sx={{ mb: 0 }}>
              {formError}
            </Alert>
          )}

          {/* 角色名稱 */}
          <Box>
            <Typography sx={{ fontWeight: 600, fontSize: 14, color: '#1e293b', mb: 0.75 }}>
              角色名稱
            </Typography>
            <TextField
              fullWidth
              size="small"
              value={roleName}
              onChange={(e) => setRoleName(e.target.value)}
              placeholder="輸入角色名稱"
              sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
            />
          </Box>

          {/* 成員 */}
          <Box>
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                mb: 1,
              }}
            >
              <Typography sx={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>
                成員
              </Typography>
              <Button
                size="small"
                variant="outlined"
                onClick={handleToggleAllUsers}
                sx={{
                  fontSize: 12,
                  borderColor: '#cbd5e1',
                  color: '#475569',
                  fontWeight: 600,
                  '&:hover': { bgcolor: '#f1f5f9' },
                }}
              >
                全選
              </Button>
            </Box>
            <Box
              sx={{
                border: '1px solid #e2e8f0',
                borderRadius: 2,
                p: 0.5,
                bgcolor: '#f8fafc',
                maxHeight: 110,
                overflowY: 'auto',
              }}
            >
              {userOptions.map((u) => (
                <Box
                  key={u.id}
                  component="label"
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.25,
                    p: '7px 10px',
                    borderRadius: 1.5,
                    cursor: 'pointer',
                    bgcolor: 'white',
                    mb: 0.5,
                    border: '1px solid #e2e8f0',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedUserIds.includes(u.id)}
                    onChange={() => handleToggleUser(u.id)}
                    style={{ width: 15, height: 15, accentColor: '#2e3f6e' }}
                  />
                  <Typography sx={{ fontSize: 13, color: '#1e293b' }}>{u.name}</Typography>
                </Box>
              ))}
              {userOptions.length === 0 && (
                <Typography sx={{ fontSize: 13, color: '#94a3b8', p: '8px 10px' }}>
                  無可用使用者
                </Typography>
              )}
            </Box>
          </Box>

          {/* 功能權限 */}
          <Box sx={{ p: 1.75, bgcolor: '#f8fafc', borderRadius: 2, border: '1px solid #e2e8f0' }}>
            <Typography sx={{ fontWeight: 700, mb: 1.5, color: '#1e293b', fontSize: 14 }}>
              功能權限
            </Typography>
            {functionOptions.map((fn, i) => (
              <Box
                key={fn.function_id}
                component="label"
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.25,
                  p: 1,
                  borderRadius: 1.5,
                  bgcolor: 'white',
                  border: '1px solid #e2e8f0',
                  mb: i < functionOptions.length - 1 ? 1 : 0,
                  cursor: 'pointer',
                }}
              >
                <input
                  type="checkbox"
                  checked={selectedFunctionIds.includes(fn.function_id)}
                  onChange={() => handleToggleFunction(fn.function_id)}
                  style={{ width: 16, height: 16, accentColor: '#2e3f6e', cursor: 'pointer' }}
                />
                <Typography component="strong" sx={{ display: 'block', fontSize: 13, fontWeight: 700 }}>
                  {fn.function_name}
                </Typography>
              </Box>
            ))}
            {functionOptions.length === 0 && (
              <Typography sx={{ fontSize: 13, color: '#94a3b8' }}>無可用功能選項</Typography>
            )}
          </Box>
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} sx={{ color: '#64748b' }} disabled={isPending}>
          取消
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          sx={{ bgcolor: '#2e3f6e', '&:hover': { bgcolor: '#1e2d52' } }}
          disabled={isPending}
        >
          {isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
