// src/pages/fn_ai_partner_tool/FnToolList.tsx
import { useState } from 'react'
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
import Chip from '@mui/material/Chip'
import { useToolsQuery, useDeleteTool } from '@/queries/useToolsQuery'
import type { ToolRow, ToolType } from '@/queries/useToolsQuery'
import FnToolForm from './FnToolForm'
import './FnToolList.css'

const TOOL_TYPE_LABEL: Record<ToolType, string> = {
  external_api: '外部 API 呼叫',
  image_extract: '圖片擷取',
  web_scraper: '網頁擷取',
}

const TOOL_TYPE_COLOR: Record<ToolType, { bg: string; color: string; border: string }> = {
  external_api: { bg: '#eff6ff', color: '#1d4ed8', border: '#bfdbfe' },
  image_extract: { bg: '#f0fdf4', color: '#166534', border: '#86efac' },
  web_scraper: { bg: '#fefce8', color: '#854d0e', border: '#fde68a' },
}

function ToolTypeBadge({ toolType }: { toolType: ToolType }) {
  const label = TOOL_TYPE_LABEL[toolType] ?? toolType
  const style = TOOL_TYPE_COLOR[toolType] ?? { bg: '#f1f5f9', color: '#475569', border: '#cbd5e1' }
  return (
    <Chip
      label={label}
      size="small"
      sx={{
        bgcolor: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
        fontWeight: 500,
        fontSize: 12,
        height: 22,
      }}
    />
  )
}

interface AppliedFilter {
  keyword?: string
}

export default function FnToolList() {
  const [filterKeyword, setFilterKeyword] = useState('')
  const [appliedFilter, setAppliedFilter] = useState<AppliedFilter>({})

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRow, setEditingRow] = useState<ToolRow | null>(null)

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [deletingRow, setDeletingRow] = useState<ToolRow | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data: tools = [], isLoading, error } = useToolsQuery(appliedFilter)
  const deleteTool = useDeleteTool()

  function handleApply() {
    const filter: AppliedFilter = {}
    if (filterKeyword.trim()) filter.keyword = filterKeyword.trim()
    setAppliedFilter(filter)
  }

  function handleAddClick() {
    setEditingRow(null)
    setIsFormOpen(true)
  }

  function handleEditClick(row: ToolRow) {
    setEditingRow(row)
    setIsFormOpen(true)
  }

  function handleDeleteClick(row: ToolRow) {
    setDeletingRow(row)
    setDeleteError(null)
    setIsDeleteDialogOpen(true)
  }

  async function handleDeleteConfirm() {
    if (!deletingRow) return
    setDeleteError(null)
    try {
      await deleteTool.mutateAsync(deletingRow.id)
      setIsDeleteDialogOpen(false)
      setDeletingRow(null)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : '刪除失敗，請稍後再試')
    }
  }

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: '工具名稱',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{value}</Typography>
      ),
    },
    {
      field: 'tool_type',
      headerName: '工具類型',
      width: 150,
      renderCell: ({ value }) => (value ? <ToolTypeBadge toolType={value as ToolType} /> : null),
    },
    {
      field: 'description',
      headerName: '工具說明',
      flex: 2,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{value}</Typography>
      ),
    },
    {
      field: 'actions',
      headerName: '執行動作',
      width: 160,
      sortable: false,
      renderCell: ({ row }: { row: ToolRow }) => (
        <Box className="fn-tool-actions-cell">
          <Button
            size="small"
            variant="outlined"
            className="fn-tool-action-btn"
            onClick={() => handleEditClick(row)}
          >
            修改
          </Button>
          <Button
            size="small"
            variant="outlined"
            className="fn-tool-action-btn-error"
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
      <Box className="fn-tool-filter-bar">
        <Box className="fn-tool-filter-group">
          <Typography className="fn-tool-filter-label">關鍵字:</Typography>
          <TextField
            size="small"
            placeholder="搜尋工具名稱..."
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
        <Button variant="outlined" size="small" onClick={handleApply} className="fn-tool-apply-btn">
          套用
        </Button>
        <Button
          variant="outlined"
          size="small"
          onClick={handleAddClick}
          className="fn-tool-add-btn"
        >
          新增
        </Button>
      </Box>

      {error ? (
        <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
      ) : (
        <Box className="fn-tool-grid-wrap">
          {isLoading ? (
            <Box className="fn-tool-loading">
              <CircularProgress />
            </Box>
          ) : (
            <DataGrid
              rows={tools}
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

      <FnToolForm
        key={editingRow?.id ?? 'new'}
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
        <DialogTitle className="fn-tool-dialog-title">確認刪除工具</DialogTitle>
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
            className="fn-tool-cancel-btn"
            disabled={deleteTool.isPending}
          >
            取消
          </Button>
          <Button onClick={handleDeleteConfirm} variant="contained" disabled={deleteTool.isPending}>
            {deleteTool.isPending ? <CircularProgress size={18} color="inherit" /> : '確認刪除'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
