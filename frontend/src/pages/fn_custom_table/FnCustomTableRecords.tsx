// src/pages/fn_custom_table/FnCustomTableRecords.tsx
import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import {
  useCustomTableRecordsQuery,
  useDeleteCustomTableRecord,
  useDeleteAllCustomTableRecords,
} from '@/queries/useCustomTableQuery'
import './FnCustomTableRecords.css'

type DeleteTarget = { type: 'single'; recordId: number } | { type: 'all' }

export default function FnCustomTableRecords() {
  const { id } = useParams<{ id: string }>()
  const tableId = Number(id)
  const navigate = useNavigate()

  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data, isLoading, error } = useCustomTableRecordsQuery(tableId)
  const deleteRecord = useDeleteCustomTableRecord()
  const deleteAllRecords = useDeleteAllCustomTableRecords()

  const tableName = data?.table_name ?? ''
  const fields = data?.fields ?? []
  const records = data?.records ?? []

  function formatDate(iso: string) {
    const d = new Date(iso)
    const yyyy = d.getFullYear()
    const mm = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const hh = String(d.getHours()).padStart(2, '0')
    const min = String(d.getMinutes()).padStart(2, '0')
    return `${yyyy}-${mm}-${dd} ${hh}:${min}`
  }

  const dynamicColumns: GridColDef[] = fields.map((f) => ({
    field: f.field_name,
    headerName: f.field_name,
    flex: 1,
    valueGetter: (_value: unknown, row: { data: Record<string, unknown> }) =>
      row.data[f.field_name] ?? '',
    renderCell: ({ value }: { value: unknown }) => (
      <Typography sx={{ fontSize: 13 }}>{String(value ?? '')}</Typography>
    ),
  }))

  const columns: GridColDef[] = [
    ...dynamicColumns,
    {
      field: 'updated_at',
      headerName: '寫入時間',
      width: 150,
      renderCell: ({ value }: { value: string }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{formatDate(value)}</Typography>
      ),
    },
    {
      field: 'actions',
      headerName: '操作',
      width: 80,
      sortable: false,
      renderCell: ({ row }: { row: { id: number } }) => (
        <Button
          size="small"
          variant="outlined"
          className="fn-records-action-btn-error"
          onClick={() => {
            setDeleteError(null)
            setDeleteTarget({ type: 'single', recordId: row.id })
          }}
        >
          刪除
        </Button>
      ),
    },
  ]

  async function handleDeleteConfirm() {
    if (!deleteTarget) return
    setDeleteError(null)
    try {
      if (deleteTarget.type === 'single') {
        await deleteRecord.mutateAsync({ tableId, recordId: deleteTarget.recordId })
      } else {
        await deleteAllRecords.mutateAsync(tableId)
      }
      setDeleteTarget(null)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : '刪除失敗，請稍後再試')
    }
  }

  const isPending = deleteRecord.isPending || deleteAllRecords.isPending

  const confirmMessage =
    deleteTarget?.type === 'all'
      ? `確定要刪除「${tableName}」的全部資料？此操作無法還原`
      : '確定要刪除此筆資料？'

  return (
    <Box>
      <Box className="fn-records-header">
        <Box className="fn-records-title-group">
          <Button
            size="small"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/custom_table')}
            className="fn-records-back-btn"
          >
            返回
          </Button>
          <Typography className="fn-records-title">{tableName}</Typography>
        </Box>
        <Button
          size="small"
          variant="outlined"
          className="fn-records-delete-all-btn"
          onClick={() => {
            setDeleteError(null)
            setDeleteTarget({ type: 'all' })
          }}
          disabled={records.length === 0}
        >
          全部刪除
        </Button>
      </Box>

      {error ? (
        <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
      ) : isLoading ? (
        <Box className="fn-records-loading">
          <CircularProgress />
        </Box>
      ) : records.length === 0 ? (
        <Box className="fn-records-empty">
          <Typography className="fn-records-empty-text">
            尚無資料，AI 夥伴使用寫入工具後，記錄將顯示於此
          </Typography>
        </Box>
      ) : (
        <Box className="fn-records-grid-wrap">
          <DataGrid
            rows={records}
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
        </Box>
      )}

      <Dialog
        open={!!deleteTarget}
        onClose={() => !isPending && setDeleteTarget(null)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle className="fn-records-dialog-title">確認刪除</DialogTitle>
        <DialogContent>
          {deleteError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {deleteError}
            </Alert>
          )}
          <Typography sx={{ fontSize: 14 }}>{confirmMessage}</Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setDeleteTarget(null)}
            className="fn-records-cancel-btn"
            disabled={isPending}
          >
            取消
          </Button>
          <Button onClick={handleDeleteConfirm} variant="contained" disabled={isPending}>
            {isPending ? <CircularProgress size={18} color="inherit" /> : '確認刪除'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
