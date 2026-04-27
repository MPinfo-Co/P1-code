import { useState } from 'react'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogContentText from '@mui/material/DialogContentText'
import DialogTitle from '@mui/material/DialogTitle'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import MenuItem from '@mui/material/MenuItem'
import Select from '@mui/material/Select'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { DataGrid, type GridColDef } from '@mui/x-data-grid'
import type { UserRow } from '@/queries/useUsersQuery'
import {
  useUsersQuery,
  useRolesOptionsQuery,
  useDeleteUser,
} from '@/queries/useUsersQuery'
import FnUserForm from './FnUserForm'

// ── Component ─────────────────────────────────────────────────────

export default function FnUserList() {
  // ── 篩選列狀態 ─────────────────────────────────────────────────
  const [filterRoleId, setFilterRoleId] = useState<number | ''>('')
  const [filterKeyword, setFilterKeyword] = useState('')
  const [applied, setApplied] = useState<{ roleId?: number; keyword?: string }>({})

  // ── 新增／修改 Dialog 狀態 ─────────────────────────────────────
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<UserRow | null>(null)

  // ── 刪除確認 Dialog 狀態 ───────────────────────────────────────
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [deletingUser, setDeletingUser] = useState<UserRow | null>(null)

  // ── Queries / Mutations ────────────────────────────────────────
  const {
    data: users = [],
    isLoading: isUsersLoading,
    isError: isUsersError,
    error: usersError,
  } = useUsersQuery({
    role_id: applied.roleId,
    keyword: applied.keyword,
  })

  const { data: roleOptions = [] } = useRolesOptionsQuery()
  const deleteUser = useDeleteUser()

  // ── Event handlers ─────────────────────────────────────────────

  function handleApply() {
    setApplied({
      roleId: filterRoleId !== '' ? filterRoleId : undefined,
      keyword: filterKeyword.trim() || undefined,
    })
  }

  function handleOpenAdd() {
    setEditingUser(null)
    setIsFormOpen(true)
  }

  function handleOpenEdit(user: UserRow) {
    setEditingUser(user)
    setIsFormOpen(true)
  }

  function handleFormClose() {
    setIsFormOpen(false)
    setEditingUser(null)
  }

  function handleFormSuccess() {
    setIsFormOpen(false)
    setEditingUser(null)
  }

  function handleOpenDelete(user: UserRow) {
    setDeletingUser(user)
    setIsDeleteOpen(true)
  }

  function handleDeleteClose() {
    setIsDeleteOpen(false)
    setDeletingUser(null)
  }

  async function handleDeleteConfirm() {
    if (!deletingUser) return
    try {
      await deleteUser.mutateAsync(deletingUser.email)
    } catch {
      // error shown via deleteUser.error if needed
    } finally {
      setIsDeleteOpen(false)
      setDeletingUser(null)
    }
  }

  // ── DataGrid columns ───────────────────────────────────────────

  const columns: GridColDef<UserRow>[] = [
    {
      field: 'name',
      headerName: '姓名',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{value}</Typography>
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
      renderCell: ({ value }: { value: UserRow['roles'] }) =>
        value?.map((r) => (
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
      renderCell: ({ row }) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant="outlined"
            onClick={() => handleOpenEdit(row)}
            sx={{ fontSize: 12, borderColor: '#cbd5e1', color: '#64748b' }}
          >
            修改
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            onClick={() => handleOpenDelete(row)}
            sx={{ fontSize: 12 }}
          >
            刪除
          </Button>
        </Box>
      ),
    },
  ]

  // ── Render ─────────────────────────────────────────────────────

  return (
    <Box>
      {/* 頁首 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 800, color: '#1e293b' }}>
          帳號管理
        </Typography>
        <Button
          variant="contained"
          onClick={handleOpenAdd}
          sx={{ bgcolor: '#2e3f6e', fontWeight: 700, fontSize: 14, '&:hover': { bgcolor: '#1e2d52' } }}
        >
          新增帳號
        </Button>
      </Box>

      {/* 篩選列 */}
      <Box
        sx={{
          bgcolor: 'white',
          borderRadius: 2,
          border: '1px solid #e2e8f0',
          p: 2,
          mb: 2,
          display: 'flex',
          gap: 2,
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>角色職位</InputLabel>
          <Select
            value={filterRoleId}
            label="角色職位"
            onChange={(e) => setFilterRoleId(e.target.value as number | '')}
          >
            <MenuItem value="">全部</MenuItem>
            {roleOptions.map((r) => (
              <MenuItem key={r.id} value={r.id}>
                {r.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          size="small"
          label="關鍵字搜尋"
          placeholder="搜尋姓名或信箱..."
          value={filterKeyword}
          onChange={(e) => setFilterKeyword(e.target.value)}
          sx={{ width: 220 }}
        />

        <Button
          variant="outlined"
          onClick={handleApply}
          sx={{ borderColor: '#2e3f6e', color: '#2e3f6e' }}
        >
          套用
        </Button>
      </Box>

      {/* API 錯誤提示 */}
      {isUsersError && (
        <Alert severity="error" sx={{ mb: 2, fontSize: 13 }}>
          {usersError instanceof Error ? usersError.message : '載入失敗，請稍後再試'}
        </Alert>
      )}

      {/* 清單表格 */}
      <Box
        sx={{ bgcolor: 'white', borderRadius: 2, border: '1px solid #e2e8f0', overflow: 'hidden' }}
      >
        <DataGrid
          rows={users}
          getRowId={(row) => row.email}
          columns={columns}
          loading={isUsersLoading}
          pageSizeOptions={[10, 25]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          disableRowSelectionOnClick
          sx={{
            border: 'none',
            '& .MuiDataGrid-columnHeaders': { bgcolor: '#f1f5f9' },
            '& .MuiDataGrid-columnHeaderTitle': { fontWeight: 800, fontSize: 14, color: '#1e293b' },
            '& .MuiDataGrid-cell': { display: 'flex', alignItems: 'center' },
            '& .MuiDataGrid-row': { borderBottom: '1px solid #f1f5f9' },
          }}
        />
      </Box>

      {/* 新增／修改 Dialog */}
      <FnUserForm
        key={`${isFormOpen}-${editingUser?.email ?? 'new'}`}
        open={isFormOpen}
        user={editingUser}
        onClose={handleFormClose}
        onSuccess={handleFormSuccess}
      />

      {/* 刪除確認 Dialog */}
      <Dialog open={isDeleteOpen} onClose={handleDeleteClose} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 800 }}>確認刪除</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ fontSize: 14 }}>
            確定要刪除 <strong>{deletingUser?.name}</strong>？此操作無法還原。
          </DialogContentText>
          {deleteUser.isError && (
            <Alert severity="error" sx={{ mt: 1.5, fontSize: 13 }}>
              {deleteUser.error instanceof Error
                ? deleteUser.error.message
                : '刪除失敗，請稍後再試'}
            </Alert>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleDeleteClose} sx={{ color: '#64748b' }} disabled={deleteUser.isPending}>
            取消
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={deleteUser.isPending}
          >
            {deleteUser.isPending ? <CircularProgress size={18} color="inherit" /> : '確認刪除'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
