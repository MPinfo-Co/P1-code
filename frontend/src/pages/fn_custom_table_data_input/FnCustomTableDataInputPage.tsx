// src/pages/fn_custom_table_data_input/FnCustomTableDataInputPage.tsx
import { useState, useRef, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
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
  useUpdateCustomTableRecord,
  useDeleteCustomTableRecord,
  useImportCustomTableRecords,
  downloadCustomTableFormat,
} from '@/queries/useCustomTableDataInputQuery'
import type { CustomTableField, CustomTableOption } from '@/queries/useCustomTableDataInputQuery'

export default function FnCustomTableDataInputPage() {
  const [selectedTable, setSelectedTable] = useState<CustomTableOption | null>(null)
  const [searchParams] = useSearchParams()
  const { data: tables = [] } = useCustomTableDataInputListQuery()

  useEffect(() => {
    const tableId = Number(searchParams.get('tableId'))
    if (tableId && tables.length > 0 && selectedTable === null) {
      const match = tables.find((t) => t.id === tableId)
      if (match) setSelectedTable(match)
    }
  }, [searchParams, tables, selectedTable])

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

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: '資料表名稱',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{value}</Typography>
      ),
    },
    {
      field: 'description',
      headerName: '說明',
      flex: 2,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{value || '—'}</Typography>
      ),
    },
    {
      field: 'actions',
      headerName: '操作',
      width: 120,
      sortable: false,
      renderCell: ({ row }: { row: CustomTableOption }) => (
        <Button
          size="small"
          variant="outlined"
          onClick={() => onSelectTable(row)}
          sx={{
            fontSize: 12,
            borderColor: '#6366f1',
            color: '#6366f1',
            '&:hover': { bgcolor: '#f0f0ff', borderColor: '#4f46e5' },
          }}
        >
          進入維護
        </Button>
      ),
    },
  ]

  return (
    <Box sx={{ px: 2.5, py: 1.75 }}>
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress size={28} />
        </Box>
      ) : tables.length === 0 ? (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            py: 6,
            bgcolor: '#f8fafc',
            borderRadius: 2,
            border: '1px solid #e2e8f0',
          }}
        >
          <Typography sx={{ fontSize: 14, color: '#64748b' }}>
            目前尚未獲得任何資料表的維護權限
          </Typography>
        </Box>
      ) : (
        <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 1, overflow: 'hidden' }}>
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
  const [inputValue, setInputValue] = useState('')
  const [keyword, setKeyword] = useState('')
  const { data, isLoading } = useCustomTableDataInputRecordsQuery(table.id, keyword)
  const deleteRecord = useDeleteCustomTableRecord()

  const [isAddOpen, setIsAddOpen] = useState(false)
  const [isEditOpen, setIsEditOpen] = useState(false)
  const [editingRecord, setEditingRecord] = useState<{
    id: number
    data: Record<string, unknown>
  } | null>(null)
  const [isImportOpen, setIsImportOpen] = useState(false)
  const [isDeleteOpen, setIsDeleteOpen] = useState(false)
  const [deletingRecordId, setDeletingRecordId] = useState<number | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const fields: CustomTableField[] = data?.fields ?? []
  const records = data?.records ?? []
  const exceeded = data?.exceeded ?? false
  const total = data?.total ?? 0

  const handleSearch = () => setKeyword(inputValue.trim())

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
      field: 'updated_by_name',
      headerName: '更新者',
      width: 100,
      valueGetter: (_value: unknown, row: { updated_by_name: string | null }) =>
        row.updated_by_name ?? '—',
    },
    {
      field: '__actions',
      headerName: '執行動作',
      width: 140,
      sortable: false,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <Button
            size="small"
            variant="outlined"
            sx={{ fontSize: 12, borderRadius: '3px' }}
            onClick={() => {
              setEditingRecord({
                id: params.row.id as number,
                data: params.row.data as Record<string, unknown>,
              })
              setIsEditOpen(true)
            }}
          >
            修改
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            sx={{ fontSize: 12, borderRadius: '3px' }}
            onClick={() => {
              setDeletingRecordId(params.row.id as number)
              setIsDeleteOpen(true)
            }}
          >
            刪除
          </Button>
        </Box>
      ),
    },
  ]

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
      {/* 標題 */}
      <Typography sx={{ fontSize: 17, fontWeight: 600, color: '#1e293b', mb: 1 }}>
        {table.name}
      </Typography>

      {/* 搜尋列 + 操作按鈕 */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          bgcolor: '#f1f5f9',
          px: '12px',
          py: '3px',
          mb: '5px',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Typography
            sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b', whiteSpace: 'nowrap' }}
          >
            關鍵字:
          </Typography>
          <TextField
            size="small"
            placeholder="輸入關鍵字查詢"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
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
          onClick={handleSearch}
          sx={{ height: 24, fontSize: 12, borderRadius: '3px' }}
        >
          查詢
        </Button>
        <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant="outlined"
            onClick={onBack}
            sx={{
              fontSize: 12,
              height: 24,
              borderRadius: '3px',
              color: '#64748b',
              borderColor: '#cbd5e1',
              '&:hover': { borderColor: '#94a3b8', bgcolor: '#f8fafc' },
            }}
          >
            返回
          </Button>
          <Button
            size="small"
            variant="outlined"
            onClick={() => setIsImportOpen(true)}
            sx={{ fontSize: 12, height: 24, borderRadius: '3px' }}
          >
            匯入 Excel
          </Button>
          <Button
            size="small"
            variant="outlined"
            onClick={() => setIsAddOpen(true)}
            sx={{ fontSize: 12, height: 24, borderRadius: '3px' }}
          >
            新增
          </Button>
        </Box>
      </Box>

      {/* 資料表格 */}
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress size={28} />
        </Box>
      ) : exceeded ? (
        <Box
          sx={{
            py: 4,
            px: 3,
            bgcolor: '#fffbeb',
            border: '1px solid #fde68a',
            borderRadius: 1,
            textAlign: 'center',
          }}
        >
          <Typography sx={{ fontSize: 14, color: '#92400e' }}>
            目前資料筆數共 {total.toLocaleString()} 筆，超過顯示上限（500 筆），請輸入關鍵字後查詢。
          </Typography>
        </Box>
      ) : records.length === 0 ? (
        <Typography sx={{ fontSize: 14, color: '#94a3b8', mt: 2 }}>
          {keyword ? '查無符合條件的資料' : '尚無資料'}
        </Typography>
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

      {/* 新增 Dialog */}
      {fields.length > 0 && (
        <AddRecordDialog
          open={isAddOpen}
          tableId={table.id}
          fields={fields}
          onClose={() => setIsAddOpen(false)}
          onSuccess={() => setIsAddOpen(false)}
        />
      )}

      {/* 修改 Dialog */}
      {fields.length > 0 && editingRecord && (
        <EditRecordDialog
          open={isEditOpen}
          tableId={table.id}
          recordId={editingRecord.id}
          initialData={editingRecord.data}
          fields={fields}
          onClose={() => {
            setIsEditOpen(false)
            setEditingRecord(null)
          }}
          onSuccess={() => {
            setIsEditOpen(false)
            setEditingRecord(null)
          }}
        />
      )}

      {/* 匯入 Excel Dialog */}
      <ImportDialog
        open={isImportOpen}
        tableId={table.id}
        tableName={table.name}
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

// ─── 修改 Dialog ──────────────────────────────────────────────────────────────

interface EditRecordDialogProps {
  open: boolean
  tableId: number
  recordId: number
  initialData: Record<string, unknown>
  fields: CustomTableField[]
  onClose: () => void
  onSuccess: () => void
}

function EditRecordDialog({
  open,
  tableId,
  recordId,
  initialData,
  fields,
  onClose,
  onSuccess,
}: EditRecordDialogProps) {
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const updateRecord = useUpdateCustomTableRecord()

  function handleChange(fieldName: string, value: string) {
    setFieldValues((prev) => ({ ...prev, [fieldName]: value }))
  }

  function handleOpen() {
    const initial: Record<string, string> = {}
    for (const f of fields) {
      initial[f.field_name] = String(initialData[f.field_name] ?? '')
    }
    setFieldValues(initial)
    setFormError(null)
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
      await updateRecord.mutateAsync({ tableId, recordId, data })
      onSuccess()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '更新失敗')
    }
  }

  return (
    <Dialog open={open} onClose={onClose} onTransitionEnter={handleOpen} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontWeight: 700 }}>修改資料</DialogTitle>
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
                sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
              />
            </Box>
          ))}
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={onClose}
          sx={{ color: '#64748b', fontSize: 13 }}
          disabled={updateRecord.isPending}
        >
          取消
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={updateRecord.isPending}
          sx={{
            bgcolor: '#2e3f6e',
            '&:hover': { bgcolor: '#1e2d52' },
            borderRadius: '3px',
            fontSize: 13,
          }}
        >
          {updateRecord.isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

// ─── 匯入 Excel Dialog ────────────────────────────────────────────────────────

interface ImportDialogProps {
  open: boolean
  tableId: number
  tableName: string
  onClose: () => void
  onSuccess: () => void
}

function ImportDialog({ open, tableId, tableName, onClose, onSuccess }: ImportDialogProps) {
  const fileRef = useRef<HTMLInputElement>(null)
  const includeDataRef = useRef<HTMLInputElement>(null)
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
    if (includeDataRef.current) includeDataRef.current.checked = false
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ fontWeight: 700 }}>匯入 Excel</DialogTitle>
      <DialogContent sx={{ pt: '16px !important' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1, flexWrap: 'wrap' }}>
              <Typography sx={{ fontSize: 12, color: '#94a3b8' }}>
                請上傳符合格式的 .xlsx 檔案。{' '}
                <Box
                  component="span"
                  onClick={() =>
                    downloadCustomTableFormat(
                      tableId,
                      tableName,
                      includeDataRef.current?.checked ?? false
                    )
                  }
                  sx={{
                    color: '#6366f1',
                    cursor: 'pointer',
                    textDecoration: 'underline',
                    '&:hover': { color: '#4f46e5' },
                  }}
                >
                  下載填寫表單
                </Box>
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <input
                  ref={includeDataRef}
                  type="checkbox"
                  id="include-data"
                  style={{ cursor: 'pointer', accentColor: '#6366f1' }}
                />
                <Typography
                  component="label"
                  htmlFor="include-data"
                  sx={{ fontSize: 12, color: '#64748b', cursor: 'pointer' }}
                >
                  包含資料（上限 1000 筆）
                </Typography>
              </Box>
            </Box>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
