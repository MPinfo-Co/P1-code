// src/pages/fn_custom_table/FnCustomTableRecords.tsx
import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Alert from '@mui/material/Alert'
import { DataGrid, type GridColDef } from '@mui/x-data-grid'
import './FnCustomTableRecords.css'
import {
  useCustomTableRecordsQuery,
  useDeleteCustomTableRecord,
  useDeleteAllCustomTableRecords,
} from '@/queries/useCustomTableQuery'

export default function FnCustomTableRecords() {
  const { id } = useParams<{ id: string }>()
  const tableId = Number(id)
  const navigate = useNavigate()

  const [alertMsg, setAlertMsg] = useState<string | null>(null)
  const [confirmDeleteRow, setConfirmDeleteRow] = useState<number | null>(null)
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false)

  const { data, isLoading } = useCustomTableRecordsQuery(tableId || null)
  const deleteRecord = useDeleteCustomTableRecord()
  const deleteAllRecords = useDeleteAllCustomTableRecords()

  const fields = data?.fields ?? []
  const records = data?.records ?? []

  const rows = records.map((r) => ({
    id: r.id,
    ...r.data,
    updated_at: new Date(r.updated_at).toLocaleString('zh-TW'),
  }))

  const dynamicColumns: GridColDef[] = fields.map((f) => ({
    field: f.field_name,
    headerName: f.field_name,
    flex: 1,
    renderCell: (params) => (
      <Typography sx={{ fontSize: 13, color: '#1e293b' }}>
        {params.value !== undefined && params.value !== null ? String(params.value) : '-'}
      </Typography>
    ),
  }))

  const columns: GridColDef[] = [
    ...dynamicColumns,
    {
      field: 'updated_at',
      headerName: '寫入時間',
      width: 180,
      renderCell: (params) => (
        <Typography sx={{ fontSize: 13, color: '#475569' }}>{params.value}</Typography>
      ),
    },
    {
      field: 'actions',
      headerName: '操作',
      width: 80,
      sortable: false,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          <Button
            size="small"
            variant="outlined"
            color="error"
            onClick={() => setConfirmDeleteRow(params.row.id as number)}
            sx={{ fontSize: 12, height: 24, borderRadius: '3px', minWidth: 'auto', px: 1 }}
          >
            刪除
          </Button>
        </Box>
      ),
    },
  ]

  async function handleDeleteRecord() {
    if (confirmDeleteRow === null) return
    const rid = confirmDeleteRow
    setConfirmDeleteRow(null)
    try {
      await deleteRecord.mutateAsync({ tableId, recordId: rid })
    } catch (err) {
      setAlertMsg(err instanceof Error ? err.message : '刪除失敗')
    }
  }

  async function handleDeleteAll() {
    setConfirmDeleteAll(false)
    try {
      await deleteAllRecords.mutateAsync(tableId)
    } catch (err) {
      setAlertMsg(err instanceof Error ? err.message : '刪除失敗')
    }
  }

  return (
    <Box sx={{ p: '14px 20px', bgcolor: '#f0f4f8', minHeight: '100vh' }}>
      <Box className="records-bar">
        <Typography className="records-bar-title">資料查看</Typography>
        <Button
          size="small"
          variant="outlined"
          className="records-bar-btn"
          onClick={() => navigate('/custom_table')}
        >
          返回
        </Button>
        <Button
          size="small"
          variant="outlined"
          color="error"
          className="records-bar-btn-danger"
          onClick={() => setConfirmDeleteAll(true)}
          disabled={rows.length === 0}
        >
          全部刪除
        </Button>
      </Box>

      {alertMsg && (
        <Alert severity="warning" onClose={() => setAlertMsg(null)} sx={{ mb: 1 }}>
          {alertMsg}
        </Alert>
      )}

      {confirmDeleteRow !== null && (
        <Alert
          severity="warning"
          action={
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                size="small"
                color="error"
                variant="contained"
                onClick={handleDeleteRecord}
                sx={{ fontSize: 12, height: 24 }}
              >
                確定刪除
              </Button>
              <Button
                size="small"
                onClick={() => setConfirmDeleteRow(null)}
                sx={{ fontSize: 12, height: 24 }}
              >
                取消
              </Button>
            </Box>
          }
          sx={{ mb: 1 }}
        >
          確定要刪除此筆記錄？此操作無法還原
        </Alert>
      )}

      {confirmDeleteAll && (
        <Alert
          severity="warning"
          action={
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                size="small"
                color="error"
                variant="contained"
                onClick={handleDeleteAll}
                sx={{ fontSize: 12, height: 24 }}
              >
                確定刪除
              </Button>
              <Button
                size="small"
                onClick={() => setConfirmDeleteAll(false)}
                sx={{ fontSize: 12, height: 24 }}
              >
                取消
              </Button>
            </Box>
          }
          sx={{ mb: 1 }}
        >
          確定要刪除所有記錄？此操作無法還原
        </Alert>
      )}

      <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 1, bgcolor: 'white' }}>
        {rows.length === 0 && !isLoading ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography sx={{ fontSize: 14, color: '#94a3b8' }}>尚無資料</Typography>
          </Box>
        ) : (
          <DataGrid
            rows={rows}
            columns={columns}
            loading={isLoading}
            rowHeight={36}
            columnHeaderHeight={36}
            disableColumnMenu
            disableRowSelectionOnClick
            autoHeight
            sx={{
              border: 'none',
              '& .MuiDataGrid-columnHeader': { bgcolor: '#f1f5f9' },
              '& .MuiDataGrid-footerContainer': { minHeight: 36 },
            }}
          />
        )}
      </Box>
    </Box>
  )
}
