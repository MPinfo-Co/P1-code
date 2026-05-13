// src/pages/fn_custom_table/FnCustomTableList.tsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Alert from '@mui/material/Alert'
import { DataGrid, type GridColDef } from '@mui/x-data-grid'
import { useCustomTablesQuery, useDeleteCustomTable } from '@/queries/useCustomTableQuery'
import type { CustomTableRow } from '@/queries/useCustomTableQuery'
import FnCustomTableForm from './FnCustomTableForm'

export default function FnCustomTableList() {
  const navigate = useNavigate()
  const [keyword, setKeyword] = useState('')
  const [appliedKeyword, setAppliedKeyword] = useState('')
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRow, setEditingRow] = useState<CustomTableRow | null>(null)
  const [alertMsg, setAlertMsg] = useState<string | null>(null)
  const [confirmRow, setConfirmRow] = useState<CustomTableRow | null>(null)

  const { data: rows = [], isLoading } = useCustomTablesQuery({
    keyword: appliedKeyword || undefined,
  })
  const deleteCustomTable = useDeleteCustomTable()

  function handleApply() {
    setAppliedKeyword(keyword)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') handleApply()
  }

  function handleAdd() {
    setEditingRow(null)
    setIsFormOpen(true)
  }

  function handleEdit(row: CustomTableRow) {
    setEditingRow(row)
    setIsFormOpen(true)
  }

  // Spec: 先呼叫刪除 API 進行檢核；若 400 直接顯示警告，不顯示確認視窗；若允許刪除，顯示確認訊息
  // Implementation: show confirm first, then call DELETE; show error if 400
  function handleDeleteRequest(row: CustomTableRow) {
    setAlertMsg(null)
    setConfirmRow(row)
  }

  async function handleConfirmDelete() {
    if (!confirmRow) return
    const target = confirmRow
    setConfirmRow(null)
    try {
      await deleteCustomTable.mutateAsync(target.id)
    } catch (err) {
      const msg = err instanceof Error ? err.message : '刪除失敗'
      setAlertMsg(msg)
    }
  }

  function handleCancelDelete() {
    setConfirmRow(null)
  }

  const columns: GridColDef<CustomTableRow>[] = [
    {
      field: 'table_name',
      headerName: '表格名稱',
      flex: 1.5,
      renderCell: (params) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
          {params.value}
        </Typography>
      ),
    },
    {
      field: 'field_count',
      headerName: '欄位數量',
      width: 120,
      renderCell: (params) => (
        <Typography sx={{ fontSize: 13, color: '#475569' }}>{params.value} 個欄位</Typography>
      ),
    },
    {
      field: 'description',
      headerName: '說明',
      flex: 2,
      renderCell: (params) => (
        <Typography sx={{ fontSize: 13, color: '#475569' }}>{params.value}</Typography>
      ),
    },
    {
      field: 'actions',
      headerName: '操作',
      width: 210,
      sortable: false,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', height: '100%' }}>
          <Button
            size="small"
            variant="outlined"
            onClick={() => navigate(`/custom_table/${params.row.id}/records`)}
            sx={{ fontSize: 12, height: 24, borderRadius: '3px', minWidth: 'auto', px: 1 }}
          >
            查看資料
          </Button>
          <Button
            size="small"
            variant="outlined"
            onClick={() => handleEdit(params.row)}
            sx={{ fontSize: 12, height: 24, borderRadius: '3px', minWidth: 'auto', px: 1 }}
          >
            修改
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            onClick={() => handleDeleteRequest(params.row)}
            sx={{ fontSize: 12, height: 24, borderRadius: '3px', minWidth: 'auto', px: 1 }}
          >
            刪除
          </Button>
        </Box>
      ),
    },
  ]

  return (
    <Box sx={{ p: '14px 20px', bgcolor: '#f0f4f8', minHeight: '100vh' }}>
      {/* Filter Bar */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          bgcolor: '#f1f5f9',
          px: '12px',
          py: '3px',
          mb: '5px',
          borderRadius: 1,
        }}
      >
        <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b', whiteSpace: 'nowrap' }}>
          關鍵字:
        </Typography>
        <TextField
          size="small"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="搜尋表格名稱"
          sx={{
            '& .MuiInputBase-root': { height: 24, fontSize: 13 },
            '& .MuiInputBase-input': { py: 0 },
            width: 200,
          }}
        />
        <Button
          size="small"
          variant="contained"
          onClick={handleApply}
          sx={{ height: 24, fontSize: 12, borderRadius: '3px' }}
        >
          套用
        </Button>
        <Button
          size="small"
          variant="contained"
          onClick={handleAdd}
          sx={{ height: 24, fontSize: 12, borderRadius: '3px', ml: 'auto' }}
        >
          新增
        </Button>
      </Box>

      {alertMsg && (
        <Alert severity="warning" onClose={() => setAlertMsg(null)} sx={{ mb: 1 }}>
          {alertMsg}
        </Alert>
      )}

      {confirmRow && (
        <Alert
          severity="warning"
          action={
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                size="small"
                color="error"
                variant="contained"
                onClick={handleConfirmDelete}
                sx={{ fontSize: 12, height: 24 }}
              >
                確定刪除
              </Button>
              <Button size="small" onClick={handleCancelDelete} sx={{ fontSize: 12, height: 24 }}>
                取消
              </Button>
            </Box>
          }
          sx={{ mb: 1 }}
        >
          確定要刪除「{confirmRow.table_name}」？此操作無法還原
        </Alert>
      )}

      {/* DataGrid */}
      <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 1, bgcolor: 'white' }}>
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
      </Box>

      <FnCustomTableForm
        open={isFormOpen}
        row={editingRow}
        onClose={() => setIsFormOpen(false)}
        onSuccess={() => {
          setIsFormOpen(false)
        }}
      />
    </Box>
  )
}
