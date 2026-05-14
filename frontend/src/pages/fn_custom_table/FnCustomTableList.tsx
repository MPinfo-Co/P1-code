// src/pages/fn_custom_table/FnCustomTableList.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
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
import Tooltip from '@mui/material/Tooltip'
import { useCustomTableQuery, useDeleteCustomTable } from '@/queries/useCustomTableQuery'
import type { CustomTableRow } from '@/queries/useCustomTableQuery'
import FnCustomTableForm from './FnCustomTableForm'
import './FnCustomTableList.css'

interface AppliedFilter {
  keyword?: string
}

export default function FnCustomTableList() {
  const navigate = useNavigate()

  const [filterKeyword, setFilterKeyword] = useState('')
  const [appliedFilter, setAppliedFilter] = useState<AppliedFilter>({})

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRow, setEditingRow] = useState<CustomTableRow | null>(null)
  const [formKey, setFormKey] = useState(0)

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [deletingRow, setDeletingRow] = useState<CustomTableRow | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data: tables = [], isLoading, error } = useCustomTableQuery(appliedFilter)
  const deleteCustomTable = useDeleteCustomTable()

  function handleApply() {
    const filter: AppliedFilter = {}
    if (filterKeyword.trim()) filter.keyword = filterKeyword.trim()
    setAppliedFilter(filter)
  }

  function handleAddClick() {
    setEditingRow(null)
    setFormKey((k) => k + 1)
    setIsFormOpen(true)
  }

  function handleEditClick(row: CustomTableRow) {
    setEditingRow(row)
    setFormKey((k) => k + 1)
    setIsFormOpen(true)
  }

  function handleViewRecordsClick(row: CustomTableRow) {
    navigate(`/custom_table/${row.id}/records`)
  }

  function handleDeleteClick(row: CustomTableRow) {
    setDeletingRow(row)
    setDeleteError(null)
    setIsDeleteDialogOpen(true)
  }

  async function handleDeleteConfirm() {
    if (!deletingRow) return
    setDeleteError(null)
    try {
      await deleteCustomTable.mutateAsync(deletingRow.id)
      setIsDeleteDialogOpen(false)
      setDeletingRow(null)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : '刪除失敗，請稍後再試')
    }
  }

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: '表格名稱',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{value}</Typography>
      ),
    },
    {
      field: 'field_count',
      headerName: '欄位數量',
      width: 120,
      renderCell: ({ value }) => <Typography sx={{ fontSize: 13 }}>{value} 個欄位</Typography>,
    },
    {
      field: 'description',
      headerName: '說明',
      flex: 2,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{value}</Typography>
      ),
    },
    {
      field: 'actions',
      headerName: '執行動作',
      width: 220,
      sortable: false,
      renderCell: ({ row }: { row: CustomTableRow }) => (
        <Box className="fn-custom-table-actions-cell">
          <Button
            size="small"
            variant="outlined"
            className="fn-custom-table-action-btn"
            onClick={() => handleViewRecordsClick(row)}
          >
            查看資料
          </Button>
          <Button
            size="small"
            variant="outlined"
            className="fn-custom-table-action-btn"
            onClick={() => handleEditClick(row)}
          >
            修改
          </Button>
          {row.is_tool_referenced ? (
            <Tooltip title="此資料表已被 AI 工具引用，請先移除相關工具的引用後再刪除" arrow>
              <span>
                <Button
                  size="small"
                  variant="outlined"
                  className="fn-custom-table-action-btn-error"
                  disabled
                >
                  刪除
                </Button>
              </span>
            </Tooltip>
          ) : (
            <Button
              size="small"
              variant="outlined"
              className="fn-custom-table-action-btn-error"
              onClick={() => handleDeleteClick(row)}
            >
              刪除
            </Button>
          )}
        </Box>
      ),
    },
  ]

  return (
    <Box>
      <Box className="fn-custom-table-filter-bar">
        <Box className="fn-custom-table-filter-group">
          <Typography className="fn-custom-table-filter-label">關鍵字:</Typography>
          <TextField
            size="small"
            placeholder="搜尋表格名稱..."
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
          className="fn-custom-table-apply-btn"
        >
          套用
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={handleAddClick}
          className="fn-custom-table-add-btn"
        >
          新增
        </Button>
      </Box>

      {error ? (
        <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
      ) : (
        <Box className="fn-custom-table-grid-wrap">
          {isLoading ? (
            <Box className="fn-custom-table-loading">
              <CircularProgress />
            </Box>
          ) : (
            <DataGrid
              rows={tables}
              columns={columns}
              getRowId={(row) => row.id}
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

      <FnCustomTableForm
        key={formKey}
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
        <DialogTitle className="fn-custom-table-dialog-title">確認刪除資料表</DialogTitle>
        <DialogContent>
          {deleteError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {deleteError}
            </Alert>
          )}
          <Typography sx={{ fontSize: 14 }}>
            確定要刪除「<strong>{deletingRow?.name}</strong>」？此操作無法還原
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setIsDeleteDialogOpen(false)}
            className="fn-custom-table-cancel-btn"
            disabled={deleteCustomTable.isPending}
          >
            取消
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            disabled={deleteCustomTable.isPending}
          >
            {deleteCustomTable.isPending ? (
              <CircularProgress size={18} color="inherit" />
            ) : (
              '確認刪除'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
