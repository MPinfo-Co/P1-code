// src/pages/fn_dept/FnDeptList.tsx
import { useState } from 'react'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import { useDeptQuery, useToggleDept } from '@/queries/useDeptQuery'
import type { DeptRow } from '@/queries/useDeptQuery'
import FnDeptForm from './FnDeptForm'
import FnDeptMembers from './FnDeptMembers'

interface AppliedFilter {
  keyword?: string
  page?: number
  page_size?: number
}

export default function FnDeptList() {
  const [filterKeyword, setFilterKeyword] = useState('')
  const [appliedFilter, setAppliedFilter] = useState<AppliedFilter>({ page: 1, page_size: 10 })

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRow, setEditingRow] = useState<DeptRow | null>(null)

  const [isMembersOpen, setIsMembersOpen] = useState(false)
  const [membersTargetId, setMembersTargetId] = useState<number | null>(null)
  const [membersTargetName, setMembersTargetName] = useState('')

  const [isToggleDialogOpen, setIsToggleDialogOpen] = useState(false)
  const [togglingRow, setTogglingRow] = useState<DeptRow | null>(null)
  const [toggleError, setToggleError] = useState<string | null>(null)

  const { data, isLoading, error } = useDeptQuery(appliedFilter)
  const toggleDept = useToggleDept()

  const rows = data?.items ?? []
  const total = data?.total ?? 0
  const currentPage = (data?.page ?? 1) - 1 // DataGrid is 0-indexed
  const pageSize = data?.page_size ?? 10

  function handleApply() {
    setAppliedFilter((prev) => ({
      ...prev,
      keyword: filterKeyword.trim() || undefined,
      page: 1,
    }))
  }

  function handleAddClick() {
    setEditingRow(null)
    setIsFormOpen(true)
  }

  function handleEditClick(row: DeptRow) {
    setEditingRow(row)
    setIsFormOpen(true)
  }

  function handleMembersClick(row: DeptRow) {
    setMembersTargetId(row.id)
    setMembersTargetName(row.name)
    setIsMembersOpen(true)
  }

  function handleToggleClick(row: DeptRow) {
    setTogglingRow(row)
    setToggleError(null)
    setIsToggleDialogOpen(true)
  }

  async function handleToggleConfirm() {
    if (!togglingRow) return
    setToggleError(null)
    try {
      await toggleDept.mutateAsync({ id: togglingRow.id, isActive: !togglingRow.is_active })
      setIsToggleDialogOpen(false)
      setTogglingRow(null)
    } catch (err) {
      setToggleError(err instanceof Error ? err.message : '操作失敗，請稍後再試')
    }
  }

  function handlePaginationChange(model: { page: number; pageSize: number }) {
    setAppliedFilter((prev) => ({
      ...prev,
      page: model.page + 1,
      page_size: model.pageSize,
    }))
  }

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: '名稱',
      flex: 1.2,
      renderCell: ({ value }) => <Typography sx={{ fontSize: 13 }}>{value}</Typography>,
    },
    {
      field: 'code',
      headerName: '代碼',
      flex: 0.8,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{value}</Typography>
      ),
    },
    {
      field: 'parent_name',
      headerName: '上級部門',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{value ?? '—'}</Typography>
      ),
    },
    {
      field: 'head_name',
      headerName: '負責人',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{value ?? '—'}</Typography>
      ),
    },
    {
      field: 'is_active',
      headerName: '狀態',
      width: 80,
      renderCell: ({ value }) => (
        <Chip
          label={value ? '啟用' : '停用'}
          size="small"
          sx={{
            fontSize: 11,
            bgcolor: value ? '#dcfce7' : '#fee2e2',
            color: value ? '#166534' : '#991b1b',
          }}
        />
      ),
    },
    {
      field: 'actions',
      headerName: '操作',
      width: 220,
      sortable: false,
      renderCell: ({ row }: { row: DeptRow }) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant="outlined"
            sx={{ fontSize: 12, borderColor: '#cbd5e1', color: '#64748b' }}
            onClick={() => handleEditClick(row)}
          >
            編輯
          </Button>
          <Button
            size="small"
            variant="outlined"
            sx={{ fontSize: 12, borderColor: '#cbd5e1', color: '#64748b' }}
            onClick={() => handleMembersClick(row)}
          >
            查看人員
          </Button>
          <Button
            size="small"
            variant="outlined"
            color={row.is_active ? 'error' : 'success'}
            sx={{ fontSize: 12 }}
            onClick={() => handleToggleClick(row)}
          >
            {row.is_active ? '停用' : '啟用'}
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
            關鍵字:
          </Typography>
          <TextField
            size="small"
            placeholder="搜尋部門名稱或代碼..."
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
          新增部門
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
              rows={rows}
              columns={columns}
              getRowId={(row) => row.id}
              rowCount={total}
              paginationMode="server"
              paginationModel={{ page: currentPage, pageSize }}
              onPaginationModelChange={handlePaginationChange}
              pageSizeOptions={[10, 25, 50]}
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
      <FnDeptForm
        key={editingRow?.id ?? 'new'}
        open={isFormOpen}
        row={editingRow}
        onClose={() => setIsFormOpen(false)}
        onSuccess={() => setIsFormOpen(false)}
      />

      {/* Members dialog */}
      <FnDeptMembers
        open={isMembersOpen}
        deptId={membersTargetId}
        deptName={membersTargetName}
        onClose={() => setIsMembersOpen(false)}
      />

      {/* Toggle confirmation dialog */}
      <Dialog
        open={isToggleDialogOpen}
        onClose={() => setIsToggleDialogOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 800 }}>
          確認{togglingRow?.is_active ? '停用' : '啟用'}
        </DialogTitle>
        <DialogContent>
          {toggleError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {toggleError}
            </Alert>
          )}
          <Typography sx={{ fontSize: 14 }}>
            確定要{togglingRow?.is_active ? '停用' : '啟用'} {togglingRow?.name}？
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setIsToggleDialogOpen(false)}
            sx={{ color: '#64748b' }}
            disabled={toggleDept.isPending}
          >
            取消
          </Button>
          <Button
            onClick={handleToggleConfirm}
            variant="contained"
            color={togglingRow?.is_active ? 'error' : 'success'}
            disabled={toggleDept.isPending}
          >
            {toggleDept.isPending ? (
              <CircularProgress size={18} color="inherit" />
            ) : togglingRow?.is_active ? (
              '停用'
            ) : (
              '啟用'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
