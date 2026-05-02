// src/pages/fn_role/FnRoleList.tsx
import { useState } from 'react'
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
import FnRoleForm from './FnRoleForm'

interface AppliedFilter {
  keyword?: string
}

export default function FnRoleList() {
  const [filterKeyword, setFilterKeyword] = useState('')
  const [appliedFilter, setAppliedFilter] = useState<AppliedFilter>({})

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRow, setEditingRow] = useState<RoleRow | null>(null)

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [deletingRow, setDeletingRow] = useState<RoleRow | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data: roles = [], isLoading, error } = useRolesQuery(appliedFilter)
  const deleteRole = useDeleteRole()

  function handleApply() {
    const filter: AppliedFilter = {}
    if (filterKeyword.trim()) filter.keyword = filterKeyword.trim()
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
          padding: '3px 12px',
          mb: '5px',
          display: 'flex',
          gap: 2,
          flexWrap: 'nowrap',
          alignItems: 'center',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography
            sx={{ fontSize: 13, color: '#1e293b', fontWeight: 700, whiteSpace: 'nowrap' }}
          >
            關鍵字搜尋:
          </Typography>
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
        <Button
          variant="outlined"
          size="small"
          onClick={handleApply}
          sx={{
            borderColor: '#2e3f6e',
            color: '#2e3f6e',
            borderRadius: '3px',
            height: 24,
            fontSize: 12,
          }}
        >
          套用
        </Button>
        <Button
          variant="contained"
          size="small"
          onClick={handleAddClick}
          sx={{ ml: 'auto', height: 24, fontSize: 12, borderRadius: '3px' }}
        >
          ＋ 新增角色
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
              rows={roles}
              columns={columns}
              getRowId={(row) => row.name}
              pageSizeOptions={[10, 25]}
              initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
              disableRowSelectionOnClick
              rowHeight={36}
              columnHeaderHeight={36}
              sx={{
                border: 'none',
                '& .MuiDataGrid-columnHeaders': { bgcolor: '#f1f5f9' },
                '& .MuiDataGrid-cell': { display: 'flex', alignItems: 'center' },
                '& .MuiDataGrid-footerContainer': { minHeight: 36, height: 36, overflow: 'hidden' },
                '& .MuiTablePagination-toolbar': { minHeight: 36, height: 36, padding: '0 8px' },
              }}
            />
          )}
        </Box>
      )}

      {/* Form dialog (new / edit) */}
      <FnRoleForm
        key={editingRow?.name ?? 'new'}
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
        <DialogTitle sx={{ fontWeight: 800 }}>確認刪除角色</DialogTitle>
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
            sx={{ color: '#64748b' }}
            disabled={deleteRole.isPending}
          >
            取消
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={deleteRole.isPending}
          >
            {deleteRole.isPending ? <CircularProgress size={18} color="inherit" /> : '確認刪除'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
