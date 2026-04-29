// src/pages/fn_user/FnUserList.tsx
import { useState } from 'react'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef, GridRenderCellParams } from '@mui/x-data-grid'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import { useUsersQuery, useDeleteUser } from '@/queries/useUsersQuery'
import type { UserRow } from '@/queries/useUsersQuery'
import { useRoleOptionsQuery } from '@/queries/useRoleOptionsQuery'
import FnUserForm from './FnUserForm'

interface AppliedFilter {
  role_id?: number
  keyword?: string
}

export default function FnUserList() {
  const [filterRole, setFilterRole] = useState<string>('all')
  const [filterKeyword, setFilterKeyword] = useState('')
  const [appliedFilter, setAppliedFilter] = useState<AppliedFilter>({})

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRow, setEditingRow] = useState<UserRow | null>(null)

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [deletingRow, setDeletingRow] = useState<UserRow | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data: users = [], isLoading, error } = useUsersQuery(appliedFilter)
  const { data: roleOptions = [] } = useRoleOptionsQuery()
  const deleteUser = useDeleteUser()

  function handleApply() {
    const filter: AppliedFilter = {}
    if (filterRole !== 'all') {
      const found = roleOptions.find((r) => r.name === filterRole)
      if (found) filter.role_id = found.id
    }
    if (filterKeyword.trim()) filter.keyword = filterKeyword.trim()
    setAppliedFilter(filter)
  }

  function handleAddClick() {
    setEditingRow(null)
    setIsFormOpen(true)
  }

  function handleEditClick(row: UserRow) {
    setEditingRow(row)
    setIsFormOpen(true)
  }

  function handleDeleteClick(row: UserRow) {
    setDeletingRow(row)
    setDeleteError(null)
    setIsDeleteDialogOpen(true)
  }

  async function handleDeleteConfirm() {
    if (!deletingRow) return
    setDeleteError(null)
    try {
      await deleteUser.mutateAsync(deletingRow.email)
      setIsDeleteDialogOpen(false)
      setDeletingRow(null)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : '刪除失敗，請稍後再試')
    }
  }

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: '名稱',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 400 }}>{value}</Typography>
      ),
    },
    {
      field: 'email',
      headerName: '電子信箱',
      flex: 1.5,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{value}</Typography>
      ),
    },
    {
      field: 'roles',
      headerName: '角色',
      flex: 1,
      sortable: false,
      renderCell: (params: GridRenderCellParams<UserRow, UserRow['roles']>) =>
        ((params.value ?? []) as UserRow['roles']).map((r) => (
          <Chip
            key={r.id}
            label={r.name}
            size="small"
            sx={{ mr: 0.5, fontSize: 11, bgcolor: '#eef1f8', color: '#2e3f6e' }}
          />
        )),
    },
    {
      field: 'actions',
      headerName: '執行動作',
      width: 160,
      sortable: false,
      renderCell: ({ row }: { row: UserRow }) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant="outlined"
            sx={{ fontSize: 12, borderColor: '#cbd5e1', color: '#64748b' }}
            onClick={() => handleEditClick(row)}
          >
            修改
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            sx={{ fontSize: 12 }}
            onClick={() => handleDeleteClick(row)}
          >
            刪除
          </Button>
        </Box>
      ),
    },
  ]

  return (
    <Box>
      {/* Filter bar */}
      <Box
        sx={{
          bgcolor: '#f1f5f9',
          borderRadius: '4px',
          padding: '5px 12px',
          mb: '5px',
          display: 'flex',
          gap: 2,
          flexWrap: 'nowrap',
          alignItems: 'center',
        }}
      >
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel sx={{ color: '#1e293b', fontWeight: 700 }}>角色職位</InputLabel>
          <Select
            value={filterRole}
            label="角色職位"
            onChange={(e) => setFilterRole(e.target.value)}
          >
            <MenuItem value="all">全部</MenuItem>
            {roleOptions.map((r) => (
              <MenuItem key={r.id} value={r.name}>
                {r.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          size="small"
          label="關鍵字搜尋"
          placeholder="搜尋名稱或信箱..."
          value={filterKeyword}
          onChange={(e) => setFilterKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleApply()}
          sx={{ width: 220 }}
          InputLabelProps={{ sx: { color: '#1e293b', fontWeight: 700 } }}
        />
        <Button
          variant="outlined"
          onClick={handleApply}
          sx={{ borderColor: '#2e3f6e', color: '#2e3f6e', borderRadius: '3px' }}
        >
          套用
        </Button>
        <Button variant="contained" onClick={handleAddClick} sx={{ ml: 'auto' }}>
          新增使用者
        </Button>
      </Box>

      {/* Data table */}
      {error ? (
        <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
      ) : (
        <Box
          sx={{
            bgcolor: 'white',
            borderRadius: '4px',
            border: '1px solid #e2e8f0',
            overflow: 'hidden',
          }}
        >
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
              <CircularProgress />
            </Box>
          ) : (
            <DataGrid
              rows={users}
              columns={columns}
              getRowId={(row) => row.email}
              pageSizeOptions={[10, 25]}
              initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
              disableRowSelectionOnClick
              sx={{
                border: 'none',
                '& .MuiDataGrid-columnHeaders': { bgcolor: '#f1f5f9' },
                '& .MuiDataGrid-cell': { display: 'flex', alignItems: 'center', py: '6px' },
              }}
            />
          )}
        </Box>
      )}

      {/* Form dialog (new / edit) */}
      <FnUserForm
        key={editingRow?.email ?? 'new'}
        open={isFormOpen}
        row={editingRow}
        onClose={() => setIsFormOpen(false)}
        onSuccess={() => setIsFormOpen(false)}
      />

      {/* Delete confirmation dialog */}
      <Dialog
        open={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 800 }}>確認刪除</DialogTitle>
        <DialogContent>
          {deleteError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {deleteError}
            </Alert>
          )}
          <Typography sx={{ fontSize: 14 }}>
            確定要刪除 {deletingRow?.name}？此操作無法還原
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setIsDeleteDialogOpen(false)}
            sx={{ color: '#64748b' }}
            disabled={deleteUser.isPending}
          >
            取消
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={deleteUser.isPending}
          >
            {deleteUser.isPending ? <CircularProgress size={18} color="inherit" /> : '刪除'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
