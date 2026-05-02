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
import { useCreateRole, useUpdateRole, useFunctionOptionsQuery } from '@/queries/useRolesQuery'
import type { RoleRow } from '@/queries/useRolesQuery'
import { useUserOptionsQuery } from '@/queries/useUserOptionsQuery'

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
  const { data: allFunctions = [] } = useFunctionOptionsQuery()

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
      <DialogTitle sx={{ fontWeight: 800 }}>{isEdit ? '編輯角色' : '新增角色'}</DialogTitle>
      <DialogContent sx={{ pt: '16px !important' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          {formError && (
            <Alert severity="error" onClose={() => setFormError(null)}>
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
              placeholder="請輸入角色名稱"
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
              <Typography sx={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>成員</Typography>
              <Button
                size="small"
                variant="outlined"
                onClick={toggleAllMembers}
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
                maxHeight: 140,
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
                    checked={selectedMemberIds.includes(u.id)}
                    onChange={() => toggleMember(u.id)}
                    style={{ width: 15, height: 15, accentColor: '#2e3f6e' }}
                  />
                  <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                    {u.name}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>

          {/* 功能權限 */}
          <Box>
            <Typography sx={{ fontWeight: 600, fontSize: 14, color: '#1e293b', mb: 1 }}>
              功能權限
            </Typography>
            <Box
              sx={{
                border: '1px solid #e2e8f0',
                borderRadius: 2,
                p: 0.5,
                bgcolor: '#f8fafc',
              }}
            >
              {allFunctions.map((fn, i) => (
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
                    mb: i < allFunctions.length - 1 ? 0.5 : 0,
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedFunctionIds.includes(fn.function_id)}
                    onChange={() => toggleFunction(fn.function_id)}
                    style={{ width: 16, height: 16, accentColor: '#2e3f6e', cursor: 'pointer' }}
                  />
                  <Box>
                    <Typography
                      component="strong"
                      sx={{ display: 'block', fontSize: 13, fontWeight: 700 }}
                    >
                      {fn.function_code}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
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
          disabled={isPending}
          sx={{ bgcolor: '#2e3f6e', '&:hover': { bgcolor: '#1e2d52' } }}
        >
          {isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
