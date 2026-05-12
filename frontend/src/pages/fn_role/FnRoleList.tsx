// src/pages/fn_role/FnRoleList.tsx
import { useState, useEffect } from 'react'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef, GridRenderCellParams } from '@mui/x-data-grid'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import { useRolesQuery, useDeleteRole } from '@/queries/useRolesQuery'
import type { RoleRow } from '@/queries/useRolesQuery'
import Pagination from '@/components/ui/Pagination'
import FnRoleForm from './FnRoleForm'
import './FnRoleList.css'

interface AppliedFilter {
  keyword?: string
}

export default function FnRoleList() {
  const [filterKeyword, setFilterKeyword] = useState('')
  const [appliedFilter, setAppliedFilter] = useState<AppliedFilter>({})
  const [page, setPage] = useState(1)
  const pageSize = 10

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRow, setEditingRow] = useState<RoleRow | null>(null)

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [deletingRow, setDeletingRow] = useState<RoleRow | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data, isLoading, error } = useRolesQuery({
    page,
    pageSize,
    ...appliedFilter,
  })
  const deleteRole = useDeleteRole()

  const roles = data?.items ?? []

  // Clamp page if total_pages decreased after mutation
  useEffect(() => {
    if (data && data.total_pages > 0 && page > data.total_pages) {
      setPage(data.total_pages)
    }
  }, [data, page])

  function handleApply() {
    const filter: AppliedFilter = {}
    if (filterKeyword.trim()) filter.keyword = filterKeyword.trim()
    setPage(1)
    setAppliedFilter(filter)
  }

  function handleAddClick() {
    setEditingRow(null)
    setIsFormOpen(true)
  }

  function handleEditClick(row: RoleRow) {
    setEditingRow(row)
    setIsFormOpen(true)
  }

  function handleDeleteClick(row: RoleRow) {
    setDeletingRow(row)
    setDeleteError(null)
    setIsDeleteDialogOpen(true)
  }

  async function handleDeleteConfirm() {
    if (!deletingRow) return
    setDeleteError(null)
    try {
      await deleteRole.mutateAsync(deletingRow.name)
      setIsDeleteDialogOpen(false)
      setDeletingRow(null)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : '刪除失敗，請稍後再試')
    }
  }

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: '角色名稱',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{value}</Typography>
      ),
    },
    {
      field: 'users',
      headerName: '使用者',
      flex: 1.5,
      sortable: false,
      renderCell: (params: GridRenderCellParams<RoleRow, RoleRow['users']>) => {
        const userList = params.value ?? []
        const display = userList.length > 0 ? userList.map((u) => u.name).join(', ') : '無'
        return <Typography sx={{ fontSize: 13, color: '#64748b' }}>{display}</Typography>
      },
    },
    {
      field: 'actions',
      headerName: '執行動作',
      width: 160,
      sortable: false,
      renderCell: ({ row }: { row: RoleRow }) => (
        <Box className="fn-role-actions-cell">
          <Button
            size="small"
            variant="outlined"
            className="fn-role-action-btn"
            onClick={() => handleEditClick(row)}
          >
            修改
          </Button>
          <Button
            size="small"
            variant="outlined"
            className="fn-role-action-btn-error"
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
      <Box className="fn-role-filter-bar">
        <Box className="fn-role-filter-group">
          <Typography className="fn-role-filter-label">關鍵字搜尋:</Typography>
          <TextField
            size="small"
            placeholder="搜尋角色名稱..."
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
        <Button variant="outlined" size="small" onClick={handleApply} className="fn-role-apply-btn">
          套用
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={handleAddClick}
          className="fn-role-add-btn"
        >
          新增
        </Button>
      </Box>

      {error ? (
        <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
      ) : (
        <Box className="fn-role-grid-wrap">
          {isLoading ? (
            <Box className="fn-role-loading">
              <CircularProgress />
            </Box>
          ) : (
            <>
              <DataGrid
                rows={roles}
                columns={columns}
                getRowId={(row) => row.name}
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

      <FnRoleForm
        key={editingRow?.name ?? 'new'}
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
        <DialogTitle className="fn-role-dialog-title">確認刪除角色</DialogTitle>
        <DialogContent>
          {deleteError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {deleteError}
            </Alert>
          )}
          <Typography sx={{ fontSize: 14 }}>
            確定要刪除角色「<strong>{deletingRow?.name}</strong>」嗎？此動作無法復原。
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setIsDeleteDialogOpen(false)}
            className="fn-role-cancel-btn"
            disabled={deleteRole.isPending}
          >
            取消
          </Button>
          <Button onClick={handleDeleteConfirm} variant="contained" disabled={deleteRole.isPending}>
            {deleteRole.isPending ? <CircularProgress size={18} color="inherit" /> : '確認刪除'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
