// src/pages/fn_user/FnUserList.tsx
import { useState, useEffect } from 'react'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef, GridRenderCellParams } from '@mui/x-data-grid'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
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
import Pagination from '@/components/ui/Pagination'
import FnUserForm from './FnUserForm'
import './FnUserList.css'

interface AppliedFilter {
  roleFilter?: number
  keyword?: string
}

export default function FnUserList() {
  const [filterRole, setFilterRole] = useState<string>('all')
  const [filterKeyword, setFilterKeyword] = useState('')
  const [appliedFilter, setAppliedFilter] = useState<AppliedFilter>({})
  const [page, setPage] = useState(1)
  const pageSize = 10

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRow, setEditingRow] = useState<UserRow | null>(null)

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [deletingRow, setDeletingRow] = useState<UserRow | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data, isLoading, error } = useUsersQuery({
    page,
    pageSize,
    ...appliedFilter,
  })
  const { data: roleOptions = [] } = useRoleOptionsQuery()

  const rawUsers = data?.items ?? []
  const users = rawUsers.map((u) => ({
    ...u,
    roles: (u.role_ids ?? [])
      .map((rid) => roleOptions.find((r) => r.id === rid))
      .filter(Boolean) as import('@/queries/useUsersQuery').RoleOption[],
  }))
  const deleteUser = useDeleteUser()

  // Clamp page if total_pages decreased after mutation
  useEffect(() => {
    if (data && data.total_pages > 0 && page > data.total_pages) {
      setPage(data.total_pages)
    }
  }, [data, page])

  function handleApply() {
    const filter: AppliedFilter = {}
    if (filterRole !== 'all') {
      const found = roleOptions.find((r) => r.name === filterRole)
      if (found) filter.roleFilter = found.id
    }
    if (filterKeyword.trim()) filter.keyword = filterKeyword.trim()
    setPage(1)
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
        <Box className="fn-user-actions-cell">
          <Button
            size="small"
            variant="outlined"
            className="fn-user-action-btn"
            onClick={() => handleEditClick(row)}
          >
            修改
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            className="fn-user-action-btn-error"
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
      <Box className="fn-user-filter-bar">
        <Box className="fn-user-filter-group">
          <Typography className="fn-user-filter-label">角色職位:</Typography>
          <Select
            value={filterRole}
            onChange={(e) => setFilterRole(e.target.value)}
            size="small"
            displayEmpty
            sx={{ height: 24, fontSize: 13, '& .MuiSelect-select': { py: '2px' } }}
          >
            <MenuItem value="all">全部</MenuItem>
            {roleOptions.map((r) => (
              <MenuItem key={r.id} value={r.name}>
                {r.name}
              </MenuItem>
            ))}
          </Select>
        </Box>
        <Box className="fn-user-filter-group">
          <Typography className="fn-user-filter-label">關鍵字:</Typography>
          <TextField
            size="small"
            placeholder="搜尋名稱或信箱..."
            value={filterKeyword}
            onChange={(e) => setFilterKeyword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleApply()}
            sx={{
              width: 200,
              '& .MuiInputBase-root': { height: 24 },
              '& .MuiInputBase-input': { py: '2px', fontSize: 13 },
            }}
          />
        </Box>
        <Button variant="outlined" size="small" onClick={handleApply} className="fn-user-apply-btn">
          套用
        </Button>
        <Button
          variant="contained"
          size="small"
          onClick={handleAddClick}
          className="fn-user-add-btn"
        >
          新增使用者
        </Button>
      </Box>

      {error ? (
        <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
      ) : (
        <Box className="fn-user-grid-wrap">
          {isLoading ? (
            <Box className="fn-user-loading">
              <CircularProgress />
            </Box>
          ) : (
            <>
              <DataGrid
                rows={users}
                columns={columns}
                getRowId={(row) => row.email}
                hideFooter
                disableRowSelectionOnClick
                rowHeight={36}
                columnHeaderHeight={36}
                sx={{
                  border: 'none',
                  '& .MuiDataGrid-columnHeaders': { bgcolor: '#f1f5f9' },
                  '& .MuiDataGrid-cell': { display: 'flex', alignItems: 'center' },
                }}
              />
              <Pagination
                page={page}
                pageSize={pageSize}
                total={data?.total ?? 0}
                onPageChange={setPage}
              />
            </>
          )}
        </Box>
      )}

      <FnUserForm
        key={editingRow?.email ?? 'new'}
        open={isFormOpen}
        row={editingRow}
        onClose={() => setIsFormOpen(false)}
        onSuccess={() => setIsFormOpen(false)}
      />

      <Dialog
        open={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle className="fn-user-dialog-title">確認刪除</DialogTitle>
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
            className="fn-user-cancel-btn"
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
