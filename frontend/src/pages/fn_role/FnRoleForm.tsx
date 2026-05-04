// src/pages/fn_role/FnRoleForm.tsx
import { useState } from 'react'
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
import { useCreateRole, useUpdateRole } from '@/queries/useRolesQuery'
import type { RoleRow } from '@/queries/useRolesQuery'
import { useUserOptionsQuery } from '@/queries/useUserOptionsQuery'
import './FnRoleForm.css'

interface Props {
  open: boolean
  row: RoleRow | null
  onClose: () => void
  onSuccess: () => void
}

export default function FnRoleForm({ open, row, onClose, onSuccess }: Props) {
  const isEdit = !!row

  const [roleName, setRoleName] = useState(() => row?.name ?? '')
  const [selectedMemberIds, setSelectedMemberIds] = useState<number[]>(
    () => row?.users.map((u) => u.id) ?? []
  )
  const [selectedFunctionIds, setSelectedFunctionIds] = useState<number[]>(
    () => row?.functions.map((f) => f.function_id) ?? []
  )
  const [formError, setFormError] = useState<string | null>(null)

  const { data: userOptions = [] } = useUserOptionsQuery()
  

  const createRole = useCreateRole()
  const updateRole = useUpdateRole()

  const isPending = createRole.isPending || updateRole.isPending

  function toggleMember(id: number) {
    setSelectedMemberIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    )
  }

  function toggleAllMembers() {
    const allIds = userOptions.map((u) => u.id)
    const isAllSelected = allIds.every((id) => selectedMemberIds.includes(id))
    setSelectedMemberIds(isAllSelected ? [] : allIds)
  }

  function toggleFunction(functionId: number) {
    setSelectedFunctionIds((prev) =>
      prev.includes(functionId) ? prev.filter((id) => id !== functionId) : [...prev, functionId]
    )
  }

  async function handleSave() {
    setFormError(null)
    if (!roleName.trim()) {
      setFormError('請輸入角色名稱')
      return
    }

    try {
      if (isEdit && row) {
        await updateRole.mutateAsync({
          roleName: row.name,
          payload: {
            name: roleName.trim(),
            member_ids: selectedMemberIds,
            function_ids: selectedFunctionIds,
          },
        })
      } else {
        await createRole.mutateAsync({
          name: roleName.trim(),
          member_ids: selectedMemberIds,
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
      <DialogTitle className="fn-role-form-title">{isEdit ? '編輯角色' : '新增角色'}</DialogTitle>
      <DialogContent sx={{ pt: '16px !important' }}>
        <Box className="fn-role-form-stack">
          {formError && (
            <Alert severity="error" onClose={() => setFormError(null)}>
              {formError}
            </Alert>
          )}

          <Box>
            <Typography className="fn-role-form-label">角色名稱</Typography>
            <TextField
              fullWidth
              size="small"
              value={roleName}
              onChange={(e) => setRoleName(e.target.value)}
              placeholder="請輸入角色名稱"
              sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
            />
          </Box>

          <Box>
            <Box className="fn-role-form-section-header">
              <Typography className="fn-role-form-label" sx={{ mb: 0 }}>
                成員
              </Typography>
              <Button
                size="small"
                variant="outlined"
                onClick={toggleAllMembers}
                className="fn-role-form-toggle-all"
              >
                全選
              </Button>
            </Box>
            <Box className="fn-role-form-members-box">
              {userOptions.map((u) => (
                <Box key={u.id} component="label" className="fn-role-form-member-row">
                  <input
                    type="checkbox"
                    checked={selectedMemberIds.includes(u.id)}
                    onChange={() => toggleMember(u.id)}
                    className="fn-role-form-checkbox"
                  />
                  <Typography className="fn-role-form-member-name">{u.name}</Typography>
                </Box>
              ))}
            </Box>
          </Box>

          <Box>
            <Typography className="fn-role-form-label">功能權限</Typography>
            
          </Box>
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} className="fn-role-form-cancel-btn" disabled={isPending}>
          取消
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={isPending}
          className="fn-role-form-save-btn"
        >
          {isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
