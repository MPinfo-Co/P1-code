// src/pages/fn_ai_partner_config/FnAiPartnerConfigList.tsx
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
import { useAiPartnerConfigQuery, useDeleteAiPartner } from '@/queries/useAiPartnerConfigQuery'
import type { AiPartnerRow } from '@/queries/useAiPartnerConfigQuery'
import FnAiPartnerConfigForm from './FnAiPartnerConfigForm'
import './FnAiPartnerConfigList.css'

interface AppliedFilter {
  keyword?: string
}

export default function FnAiPartnerConfigList() {
  const [filterKeyword, setFilterKeyword] = useState('')
  const [appliedFilter, setAppliedFilter] = useState<AppliedFilter>({})

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRow, setEditingRow] = useState<AiPartnerRow | null>(null)

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [deletingRow, setDeletingRow] = useState<AiPartnerRow | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data: partners = [], isLoading, error } = useAiPartnerConfigQuery(appliedFilter)
  const deletePartner = useDeleteAiPartner()

  function handleApply() {
    const filter: AppliedFilter = {}
    if (filterKeyword.trim()) filter.keyword = filterKeyword.trim()
    setAppliedFilter(filter)
  }

  function handleAddClick() {
    setEditingRow(null)
    setIsFormOpen(true)
  }

  function handleEditClick(row: AiPartnerRow) {
    setEditingRow(row)
    setIsFormOpen(true)
  }

  function handleDeleteClick(row: AiPartnerRow) {
    setDeletingRow(row)
    setDeleteError(null)
    setIsDeleteDialogOpen(true)
  }

  async function handleDeleteConfirm() {
    if (!deletingRow) return
    setDeleteError(null)
    try {
      await deletePartner.mutateAsync(deletingRow.id)
      setIsDeleteDialogOpen(false)
      setDeletingRow(null)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : '刪除失敗，請稍後再試')
    }
  }

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: '夥伴名稱',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{value}</Typography>
      ),
    },
    {
      field: 'description',
      headerName: '描述',
      flex: 2,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{value}</Typography>
      ),
    },
    {
      field: 'is_enabled',
      headerName: '狀態',
      width: 90,
      renderCell: ({ value }) => (
        <Chip
          label={value ? '啟用' : '停用'}
          size="small"
          sx={{
            fontSize: 12,
            height: 22,
            bgcolor: value ? '#dcfce7' : '#f1f5f9',
            color: value ? '#166534' : '#475569',
            fontWeight: 600,
          }}
        />
      ),
    },
    {
      field: 'actions',
      headerName: '執行動作',
      width: 160,
      sortable: false,
      renderCell: ({ row }: { row: AiPartnerRow }) => (
        <Box className="fn-ai-partner-config-actions-cell">
          <Button
            size="small"
            variant="outlined"
            className="fn-ai-partner-config-action-btn"
            onClick={() => handleEditClick(row)}
          >
            修改
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            className="fn-ai-partner-config-action-btn-error"
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
      <Box className="fn-ai-partner-config-filter-bar">
        <Box className="fn-ai-partner-config-filter-group">
          <Typography className="fn-ai-partner-config-filter-label">關鍵字:</Typography>
          <TextField
            size="small"
            placeholder="搜尋夥伴名稱、描述..."
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
          className="fn-ai-partner-config-apply-btn"
        >
          套用
        </Button>
        <Button
          variant="contained"
          size="small"
          onClick={handleAddClick}
          className="fn-ai-partner-config-add-btn"
        >
          ＋ 新增夥伴
        </Button>
      </Box>

      {error ? (
        <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
      ) : (
        <Box className="fn-ai-partner-config-grid-wrap">
          {isLoading ? (
            <Box className="fn-ai-partner-config-loading">
              <CircularProgress />
            </Box>
          ) : (
            <DataGrid
              rows={partners}
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

      <FnAiPartnerConfigForm
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
        <DialogTitle className="fn-ai-partner-config-dialog-title">確認刪除夥伴</DialogTitle>
        <DialogContent>
          {deleteError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {deleteError}
            </Alert>
          )}
          <Typography sx={{ fontSize: 14 }}>
            確定要刪除「<strong>{deletingRow?.name}</strong>」？此操作無法還原。
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setIsDeleteDialogOpen(false)}
            className="fn-ai-partner-config-cancel-btn"
            disabled={deletePartner.isPending}
          >
            取消
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={deletePartner.isPending}
          >
            {deletePartner.isPending ? <CircularProgress size={18} color="inherit" /> : '確認刪除'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
