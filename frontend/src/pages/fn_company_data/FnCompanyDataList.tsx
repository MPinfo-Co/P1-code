// src/pages/fn_company_data/FnCompanyDataList.tsx
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
import { useCompanyDataQuery, useDeleteCompanyData } from '@/queries/useCompanyDataQuery'
import type { CompanyDataRow } from '@/queries/useCompanyDataQuery'
import FnCompanyDataForm from './FnCompanyDataForm'

interface AppliedFilter {
  keyword?: string
}

export default function FnCompanyDataList() {
  const [filterKeyword, setFilterKeyword] = useState('')
  const [appliedFilter, setAppliedFilter] = useState<AppliedFilter>({})

  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingRow, setEditingRow] = useState<CompanyDataRow | null>(null)

  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [deletingRow, setDeletingRow] = useState<CompanyDataRow | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const { data: rows = [], isLoading, error } = useCompanyDataQuery(appliedFilter)
  const deleteCompanyData = useDeleteCompanyData()

  function handleApply() {
    const filter: AppliedFilter = {}
    if (filterKeyword.trim()) filter.keyword = filterKeyword.trim()
    setAppliedFilter(filter)
  }

  function handleAddClick() {
    setEditingRow(null)
    setIsFormOpen(true)
  }

  function handleEditClick(row: CompanyDataRow) {
    setEditingRow(row)
    setIsFormOpen(true)
  }

  function handleDeleteClick(row: CompanyDataRow) {
    setDeletingRow(row)
    setDeleteError(null)
    setIsDeleteDialogOpen(true)
  }

  async function handleDeleteConfirm() {
    if (!deletingRow) return
    setDeleteError(null)
    try {
      await deleteCompanyData.mutateAsync(deletingRow.id)
      setIsDeleteDialogOpen(false)
      setDeletingRow(null)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : '刪除失敗，請稍後再試')
    }
  }

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: '資料名稱',
      flex: 1,
      minWidth: 150,
      renderCell: (params: GridRenderCellParams<CompanyDataRow>) => (
        <Typography sx={{ fontSize: 13, fontWeight: 700 }}>{params.value}</Typography>
      ),
    },
    {
      field: 'content',
      headerName: '內容',
      flex: 2,
      minWidth: 200,
      renderCell: (params: GridRenderCellParams<CompanyDataRow>) => {
        const lines = (params.value as string)
          .split('\n')
          .filter((line: string) => line.trim() !== '')
        return (
          <Box sx={{ py: 0.5 }}>
            {lines.map((line: string, idx: number) => (
              <Typography key={idx} sx={{ fontSize: 13 }}>
                {line}
              </Typography>
            ))}
          </Box>
        )
      },
    },
    {
      field: 'partners',
      headerName: '適用夥伴',
      flex: 1,
      minWidth: 150,
      renderCell: (params: GridRenderCellParams<CompanyDataRow>) => {
        const partners = params.row.partners as CompanyDataRow['partners']
        if (!partners || partners.length === 0) {
          return <Typography sx={{ fontSize: 13, color: '#94a3b8' }}>—</Typography>
        }
        return (
          <Typography sx={{ fontSize: 13 }}>
            {partners.map((p) => p.name).join('、')}
          </Typography>
        )
      },
    },
    {
      field: 'actions',
      headerName: '執行動作',
      width: 140,
      sortable: false,
      renderCell: (params: GridRenderCellParams<CompanyDataRow>) => (
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', height: '100%' }}>
          <Button
            size="small"
            variant="outlined"
            onClick={() => handleEditClick(params.row)}
            sx={{ fontSize: 12, height: 24, minWidth: 40, borderRadius: '3px' }}
          >
            修改
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            onClick={() => handleDeleteClick(params.row)}
            sx={{ fontSize: 12, height: 24, minWidth: 40, borderRadius: '3px' }}
          >
            刪除
          </Button>
        </Box>
      ),
    },
  ]

  return (
    <Box sx={{ px: '20px', py: '14px', bgcolor: '#f0f4f8', minHeight: '100%' }}>
      <Typography sx={{ fontSize: 18, fontWeight: 700, mb: 1.5, color: '#1e293b' }}>
        公司資料
      </Typography>

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
          placeholder="搜尋資料名稱、內容、適用夥伴..."
          value={filterKeyword}
          onChange={(e) => setFilterKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleApply()}
          sx={{
            width: 260,
            '& .MuiInputBase-root': { height: 24 },
            '& .MuiInputBase-input': { py: '2px', fontSize: 13 },
          }}
        />
        <Button
          variant="outlined"
          size="small"
          onClick={handleApply}
          sx={{ height: 24, fontSize: 12, borderRadius: '3px' }}
        >
          套用
        </Button>
        <Button
          variant="contained"
          size="small"
          onClick={handleAddClick}
          sx={{ height: 24, fontSize: 12, borderRadius: '3px', ml: 'auto' }}
        >
          新增資料
        </Button>
      </Box>

      {error ? (
        <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
      ) : (
        <Box
          sx={{
            bgcolor: 'white',
            border: '1px solid #e2e8f0',
            borderRadius: 1,
            overflow: 'hidden',
          }}
        >
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <DataGrid
              rows={rows}
              columns={columns}
              getRowId={(row) => row.id}
              pageSizeOptions={[10, 25]}
              initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
              disableRowSelectionOnClick
              rowHeight={36}
              columnHeaderHeight={36}
              getRowHeight={() => 'auto'}
              localeText={{ noRowsLabel: '沒有符合條件的資料' }}
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

      <FnCompanyDataForm
        key={editingRow?.id ?? 'new'}
        open={isFormOpen}
        row={editingRow}
        onClose={() => setIsFormOpen(false)}
        onSuccess={() => setIsFormOpen(false)}
      />

      {/* Delete Confirm Dialog */}
      <Dialog
        open={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle sx={{ fontSize: 16, fontWeight: 600 }}>確認刪除</DialogTitle>
        <DialogContent>
          {deleteError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {deleteError}
            </Alert>
          )}
          <Typography sx={{ fontSize: 14 }}>
            確定要刪除「{deletingRow?.name}」？
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button
            onClick={() => setIsDeleteDialogOpen(false)}
            disabled={deleteCompanyData.isPending}
          >
            取消
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            variant="contained"
            color="error"
            disabled={deleteCompanyData.isPending}
          >
            {deleteCompanyData.isPending ? <CircularProgress size={18} color="inherit" /> : '確認'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
