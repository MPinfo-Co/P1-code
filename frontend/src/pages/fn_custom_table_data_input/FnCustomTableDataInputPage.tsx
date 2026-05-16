// src/pages/fn_custom_table_data_input/FnCustomTableDataInputPage.tsx
import { useState, useRef } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Card from '@mui/material/Card'
import CardActionArea from '@mui/material/CardActionArea'
import CardContent from '@mui/material/CardContent'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import TextField from '@mui/material/TextField'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import {
  useCustomTableDataInputListQuery,
  useCustomTableDataInputRecordsQuery,
  useAddCustomTableRecord,
  useDeleteCustomTableRecord,
  useImportCustomTableRecords,
  downloadCustomTableFormat,
} from '@/queries/useCustomTableDataInputQuery'
import type { CustomTableField, CustomTableOption } from '@/queries/useCustomTableDataInputQuery'

export default function FnCustomTableDataInputPage() {
  const [selectedTable, setSelectedTable] = useState<CustomTableOption | null>(null)

  if (selectedTable === null) {
    return <TableListView onSelectTable={setSelectedTable} />
  }
  return <TableDataView table={selectedTable} onBack={() => setSelectedTable(null)} />
}

// ─── 第一層：授權表清單 ───────────────────────────────────────────────────────

interface TableListViewProps {
  onSelectTable: (table: CustomTableOption) => void
}

function TableListView({ onSelectTable }: TableListViewProps) {
  const { data: tables = [], isLoading } = useCustomTableDataInputListQuery()

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={28} />
      </Box>
    )
  }

  return (
    <Box sx={{ px: 2.5, py: 1.75 }}>
      <Typography sx={{ fontSize: 17, fontWeight: 700, color: '#1e293b', mb: 0.5 }}>
        資料表維護
      </Typography>
      <Typography sx={{ fontSize: 13, color: '#64748b', mb: 2 }}>
        選擇要維護的資料表，可新增、匯入或刪除記錄。
      </Typography>

      {tables.length === 0 ? (
        <Typography sx={{ fontSize: 14, color: '#94a3b8', mt: 3 }}>
          目前尚未獲得任何資料表的維護權限
        </Typography>
      ) : (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
            gap: 2,
          }}
        >
          {tables.map((table) => (
            <Card
              key={table.id}
              variant="outlined"
              sx={{ borderColor: '#e2e8f0', borderRadius: 2 }}
            >
              <CardActionArea onClick={() => onSelectTable(table)} sx={{ p: 0 }}>
                <CardContent>
                  <Typography sx={{ fontSize: 15, fontWeight: 600, color: '#1e293b', mb: 0.5 }}>
                    {table.name}
                  </Typography>
                  <Typography sx={{ fontSize: 13, color: '#64748b' }}>
                    {table.description || '（無說明）'}
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  )
}

// ─── 第二層：單表資料頁 ───────────────────────────────────────────────────────

interface TableDataViewProps {
  table: CustomTableOption
  onBack: () => void
}

function TableDataView({ table, onBack }: TableDataViewProps) {
  const { data, isLoading } = useCustomTableDataInputRecordsQuery(table.id)
  const deleteRecord = useDeleteCustomTableRecord()

  const [isAddOpen, setIsAddOpen] = useState(false)
  const [isImportOpen, setIsImportOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [deletingRecordId, setDeletingRecordId] = useState<number | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)

  const fields: CustomTableField[] = data?.fields ?? []
  const records = data?.records ?? []

  const columns: GridColDef[] = [
    ...fields.map((f) => ({
      field: f.field_name,
      headerName: f.field_name,
      flex: 1,
      minWidth: 100,
      valueGetter: (_value: unknown, row: { data: Record<string, unknown> }) =>
        row.data?.[f.field_name] ?? '',
    })),
    {
      field: '__actions',
      headerName: '',
      width: 80,
      sortable: false,
      renderCell: (params) => (
        <Button
          size="small"
          color="error"
          variant="outlined"
          sx={{ fontSize: 12, height: 26, minWidth: 48 }}
          onClick={() => {
            setDeletingRecordId(params.row.id as number)
            setIsDeleteOpen(true)
          }}
        >
          刪除
        </Button>
      ),
    },
  ]

  async function handleDownloadFormat() {
    setIsDownloading(true)
    try {
      await downloadCustomTableFormat(table.id)
    } catch {
      // silently ignore download errors
    } finally {
      setIsDownloading(false)
    }
  }

  async function handleConfirmDelete() {
    if (deletingRecordId === null) return
    setDeleteError(null)
    try {
      await deleteRecord.mutateAsync({ tableId: table.id, recordId: deletingRecordId })
      setIsDeleteOpen(false)
      setDeletingRecordId(null)
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : '刪除失敗')
    }
  }

  return (
    <Box sx={{ px: 2.5, py: 1.75 }}>
      {/* 返回連結 */}
      <Box
        component="span"
        onClick={onBack}
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 0.5,
          fontSize: 13,
          color: '#475569',
          cursor: 'pointer',
          mb: 1.5,
          '&:hover': { color: '#1e293b' },
        }}
      >
        ← 返回
      </Box>

      {/* 標題列 + 操作按鈕 */}
      <Box
        sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.75 }}
      >
        <Typography sx={{ fontSize: 17, fontWeight: 600, color: '#1e293b' }}>
          {table.name}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant="outlined"
            disabled={isDownloading}
            onClick={handleDownloadFormat}
            sx={{ fontSize: 12, height: 28, borderColor: '#cbd5e1', color: '#475569' }}
          >
            {isDownloading ? <CircularProgress size={14} /> : '下載格式'}
          </Button>
          <Button
            size="small"
            variant="outlined"
            onClick={() => setIsImportOpen(true)}
            sx={{ fontSize: 12, height: 28, borderColor: '#cbd5e1', color: '#475569' }}
          >
            匯入 Excel
          </Button>
          <Button
            size="small"
            variant="contained"
            onClick={() => setIsAddOpen(true)}
            sx={{
              fontSize: 12,
              height: 28,
              bgcolor: '#2e3f6e',
              '&:hover': { bgcolor: '#1e2d52' },
            }}
          >
            新增筆數
          </Button>
        </Box>
      </Box>

      {/* 資料表格 */}
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress size={28} />
        </Box>
      ) : records.length === 0 ? (
        <Typography sx={{ fontSize: 14, color: '#94a3b8', mt: 2 }}>尚無資料</Typography>
      ) : (
        <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 1 }}>
          <DataGrid
            rows={records}
            columns={columns}
            rowHeight={36}
            columnHeaderHeight={36}
            disableRowSelectionOnClick
            hideFooterSelectedRowCount
            sx={{
              border: 'none',
              '& .MuiDataGrid-columnHeaders': { bgcolor: '#f1f5f9' },
              '& .MuiDataGrid-footerContainer': { minHeight: 36 },
            }}
          />
        </Box>
      )}

      {/* 新增筆數 Dialog */}
      {fields.length > 0 && (
        <AddRecordDialog
          open={isAddOpen}
          tableId={table.id}
          fields={fields}
          onClose={() => setIsAddOpen(false)}
          onSuccess={() => setIsAddOpen(false)}
        />
      )}

      {/* 匯入 Excel Dialog */}
      <ImportDialog
        open={isImportOpen}
        tableId={table.id}
        onClose={() => setIsImportOpen(false)}
        onSuccess={() => setIsImportOpen(false)}
      />

      {/* 刪除確認 Dialog */}
      <Dialog open={isDeleteOpen} onClose={() => setIsDeleteOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontWeight: 700, color: '#b91c1c' }}>確認刪除</DialogTitle>
        <DialogContent>
          <Typography sx={{ fontSize: 13, color: '#475569', lineHeight: 1.6 }}>
            確定要刪除這筆資料嗎？此動作無法復原。
          </Typography>
          {deleteError && (
            <Alert severity="error" sx={{ mt: 1 }} onClose={() => setDeleteError(null)}>
              {deleteError}
            </Alert>
          )}
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setIsDeleteOpen(false)} sx={{ color: '#64748b' }}>
            取消
          </Button>
          <Button
            onClick={handleConfirmDelete}
            variant="contained"
            color="error"
            disabled={deleteRecord.isPending}
          >
            {deleteRecord.isPending ? <CircularProgress size={18} color="inherit" /> : '確認刪除'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

// ─── 新增筆數 Dialog ──────────────────────────────────────────────────────────

interface AddRecordDialogProps {
  open: boolean
  tableId: number
  fields: CustomTableField[]
  onClose: () => void
  onSuccess: () => void
}

function AddRecordDialog({ open, tableId, fields, onClose, onSuccess }: AddRecordDialogProps) {
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const addRecord = useAddCustomTableRecord()

  function handleChange(fieldName: string, value: string) {
    setFieldValues((prev) => ({ ...prev, [fieldName]: value }))
  }

  async function handleSave() {
    setFormError(null)
    const data: Record<string, unknown> = {}
    for (const f of fields) {
      const raw = fieldValues[f.field_name] ?? ''
      if (f.field_type === 'number') {
        const num = Number(raw)
        if (raw !== '' && isNaN(num)) {
          setFormError(`欄位「${f.field_name}」須為數值`)
          return
        }
        data[f.field_name] = raw === '' ? null : num
      } else {
        data[f.field_name] = raw
      }
    }
    try {
      await addRecord.mutateAsync({ tableId, data })
      setFieldValues({})
      onSuccess()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '新增失敗')
    }
  }

  function handleClose() {
    setFieldValues({})
    setFormError(null)
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontWeight: 700 }}>新增筆數</DialogTitle>
      <DialogContent sx={{ pt: '16px !important' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {formError && (
            <Alert severity="error" onClose={() => setFormError(null)}>
              {formError}
            </Alert>
          )}
          {fields.map((f) => (
            <Box key={f.id}>
              <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b', mb: 0.5 }}>
                {f.field_name}
              </Typography>
              <TextField
                fullWidth
                size="small"
                type={f.field_type === 'number' ? 'number' : 'text'}
                value={fieldValues[f.field_name] ?? ''}
                onChange={(e) => handleChange(f.field_name, e.target.value)}
                placeholder={f.field_type === 'number' ? '請輸入數值' : '請輸入文字'}
                sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
              />
            </Box>
          ))}
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose} sx={{ color: '#64748b' }} disabled={addRecord.isPending}>
          取消
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={addRecord.isPending}
          sx={{ bgcolor: '#2e3f6e', '&:hover': { bgcolor: '#1e2d52' } }}
        >
          {addRecord.isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

// ─── 匯入 Excel Dialog ────────────────────────────────────────────────────────

interface ImportDialogProps {
  open: boolean
  tableId: number
  onClose: () => void
  onSuccess: () => void
}

function ImportDialog({ open, tableId, onClose, onSuccess }: ImportDialogProps) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [importError, setImportError] = useState<string | null>(null)
  const [importSuccess, setImportSuccess] = useState(false)
  const importRecords = useImportCustomTableRecords()

  async function handleImport() {
    const file = fileRef.current?.files?.[0]
    if (!file) {
      setImportError('請選擇檔案')
      return
    }
    setImportError(null)
    setImportSuccess(false)
    try {
      await importRecords.mutateAsync({ tableId, file })
      setImportSuccess(true)
      onSuccess()
    } catch (err) {
      setImportError(err instanceof Error ? err.message : '匯入失敗')
    }
  }

  function handleClose() {
    setImportError(null)
    setImportSuccess(false)
    if (fileRef.current) fileRef.current.value = ''
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontWeight: 700 }}>匯入 Excel</DialogTitle>
      <DialogContent sx={{ pt: '16px !important' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Typography sx={{ fontSize: 13, color: '#475569', lineHeight: 1.6 }}>
            請上傳符合格式的 .xlsx 檔案。
            <br />
            所有列必須通過驗證才會寫入（all-or-nothing）；若有錯誤，將顯示錯誤列號。
          </Typography>
          <Box>
            <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b', mb: 0.5 }}>
              選擇檔案
            </Typography>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx"
              style={{ fontSize: 13, color: '#1e293b' }}
            />
          </Box>
          {importError && (
            <Alert severity="error" onClose={() => setImportError(null)}>
              {importError}
            </Alert>
          )}
          {importSuccess && <Alert severity="success">匯入成功</Alert>}
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose} sx={{ color: '#64748b' }} disabled={importRecords.isPending}>
          取消
        </Button>
        <Button
          onClick={handleImport}
          variant="contained"
          disabled={importRecords.isPending}
          sx={{ bgcolor: '#2e3f6e', '&:hover': { bgcolor: '#1e2d52' } }}
        >
          {importRecords.isPending ? <CircularProgress size={18} color="inherit" /> : '匯入'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
