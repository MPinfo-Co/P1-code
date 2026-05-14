// src/pages/fn_custom_table/FnCustomTableForm.tsx
import { useState } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import IconButton from '@mui/material/IconButton'
import Alert from '@mui/material/Alert'
import CircularProgress from '@mui/material/CircularProgress'
import LockOutlinedIcon from '@mui/icons-material/LockOutlined'
import {
  useCreateCustomTable,
  useUpdateCustomTable,
  useCustomTableOptionsQuery,
} from '@/queries/useCustomTableQuery'
import type { CustomTableRow, CustomTableField } from '@/queries/useCustomTableQuery'

interface Props {
  open: boolean
  row: CustomTableRow | null
  onClose: () => void
  onSuccess: () => void
}

interface FieldRow extends CustomTableField {
  isOriginal: boolean
}

/**
 * Inner form rendered with a stable key so state resets when row changes.
 */
interface InnerProps extends Props {
  initialTableName: string
  initialDescription: string
  initialFields: FieldRow[]
}

function FnCustomTableFormInner({
  open,
  row,
  onClose,
  onSuccess,
  initialTableName,
  initialDescription,
  initialFields,
}: InnerProps) {
  const isEdit = !!row

  const [tableName, setTableName] = useState(initialTableName)
  const [description, setDescription] = useState(initialDescription)
  const [fields, setFields] = useState<FieldRow[]>(initialFields)
  const [formError, setFormError] = useState<string | null>(null)

  const createCustomTable = useCreateCustomTable()
  const updateCustomTable = useUpdateCustomTable()

  const isPending = createCustomTable.isPending || updateCustomTable.isPending

  function handleAddField() {
    setFields((prev) => [
      ...prev,
      { field_name: '', field_type: 'string', description: '', isOriginal: false },
    ])
  }

  function handleRemoveField(index: number) {
    setFields((prev) => prev.filter((_, i) => i !== index))
  }

  function handleFieldChange(index: number, key: keyof FieldRow, value: string) {
    setFields((prev) => prev.map((f, i) => (i === index ? { ...f, [key]: value } : f)))
  }

  async function handleSave() {
    setFormError(null)

    if (!tableName.trim()) {
      setFormError('請填寫表格名稱')
      return
    }
    if (fields.length === 0) {
      setFormError('至少須定義一個欄位')
      return
    }
    for (const f of fields) {
      if (!f.field_name.trim()) {
        setFormError('欄位名稱不可為空')
        return
      }
    }

    const payload = {
      name: tableName.trim(),
      description: description.trim(),
      fields: fields.map((f) => ({
        field_name: f.field_name.trim(),
        field_type: f.field_type,
        description: f.description?.trim() ?? '',
      })),
    }

    try {
      if (isEdit && row) {
        await updateCustomTable.mutateAsync({ id: row.id, payload })
      } else {
        await createCustomTable.mutateAsync(payload)
      }
      onSuccess()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '操作失敗，請稍後再試')
    }
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ fontSize: 16, fontWeight: 600 }}>
        {isEdit ? '編輯自訂資料表' : '新增自訂資料表'}
      </DialogTitle>
      <DialogContent sx={{ pt: '16px !important' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {formError && (
            <Alert severity="error" onClose={() => setFormError(null)}>
              {formError}
            </Alert>
          )}

          {/* 基本資訊 */}
          <Typography sx={{ fontSize: 14, fontWeight: 600, color: '#1e293b' }}>基本資訊</Typography>

          <Box>
            <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#334155', mb: 0.5 }}>
              表格名稱 <span style={{ color: '#ef4444' }}>*</span>
            </Typography>
            <TextField
              fullWidth
              size="small"
              value={tableName}
              onChange={(e) => setTableName(e.target.value)}
              placeholder="請輸入表格名稱"
              sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
            />
          </Box>

          <Box>
            <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#334155', mb: 0.5 }}>
              說明
            </Typography>
            <TextField
              fullWidth
              size="small"
              multiline
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="描述此資料表的用途"
              sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
            />
          </Box>

          {/* 欄位定義 */}
          <Box>
            <Typography sx={{ fontSize: 14, fontWeight: 600, color: '#1e293b', mb: 1 }}>
              欄位定義
            </Typography>
            <Typography sx={{ fontSize: 12, color: '#64748b', mb: 1 }}>
              至少須定義一個欄位才可儲存
              {isEdit && (
                <span style={{ marginLeft: 8, color: '#f59e0b' }}>
                  已有紀錄的欄位（🔒）不可修改欄位名稱、型別，且無法刪除
                </span>
              )}
            </Typography>

            {/* Column headers */}
            {fields.length > 0 && (
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 120px 1fr 40px',
                  gap: 1,
                  px: 0.5,
                  mb: 0.5,
                }}
              >
                <Typography sx={{ fontSize: 12, fontWeight: 600, color: '#64748b' }}>
                  欄位名稱
                </Typography>
                <Typography sx={{ fontSize: 12, fontWeight: 600, color: '#64748b' }}>
                  型別
                </Typography>
                <Typography sx={{ fontSize: 12, fontWeight: 600, color: '#64748b' }}>
                  欄位說明
                </Typography>
                <Box />
              </Box>
            )}

            {fields.map((field, index) => (
              <Box
                key={index}
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 120px 1fr 40px',
                  gap: 1,
                  mb: 1,
                  alignItems: 'center',
                }}
              >
                <TextField
                  size="small"
                  placeholder="欄位名稱"
                  value={field.field_name}
                  onChange={(e) => handleFieldChange(index, 'field_name', e.target.value)}
                  disabled={field.isOriginal}
                  sx={{ '& .MuiInputBase-input': { fontSize: 13 } }}
                />
                <Select
                  size="small"
                  value={field.field_type}
                  onChange={(e) =>
                    handleFieldChange(index, 'field_type', e.target.value as 'string' | 'number')
                  }
                  disabled={field.isOriginal}
                  sx={{ fontSize: 13 }}
                >
                  <MenuItem value="string" sx={{ fontSize: 13 }}>
                    string
                  </MenuItem>
                  <MenuItem value="number" sx={{ fontSize: 13 }}>
                    number
                  </MenuItem>
                </Select>
                <TextField
                  size="small"
                  placeholder="欄位說明"
                  value={field.description}
                  onChange={(e) => handleFieldChange(index, 'description', e.target.value)}
                  sx={{ '& .MuiInputBase-input': { fontSize: 13 } }}
                />
                {field.isOriginal ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <LockOutlinedIcon sx={{ fontSize: 18, color: '#94a3b8' }} />
                  </Box>
                ) : (
                  <IconButton
                    size="small"
                    onClick={() => handleRemoveField(index)}
                    aria-label="刪除欄位"
                    sx={{ color: '#ef4444' }}
                  >
                    ×
                  </IconButton>
                )}
              </Box>
            ))}

            <Button
              variant="outlined"
              size="small"
              onClick={handleAddField}
              sx={{ mt: 0.5, fontSize: 12 }}
            >
              ＋ 新增欄位
            </Button>
          </Box>
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={isPending} sx={{ fontSize: 13 }}>
          取消
        </Button>
        <Button onClick={handleSave} variant="contained" disabled={isPending} sx={{ fontSize: 13 }}>
          {isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

/**
 * Outer wrapper: resolves initial field data from options API before rendering inner form.
 * Uses a key derived from `row?.id` so the inner form state resets when switching rows.
 */
export default function FnCustomTableForm({ open, row, onClose, onSuccess }: Props) {
  const { data: tableOptions = [] } = useCustomTableOptionsQuery()

  const isEdit = !!row
  let initialTableName = ''
  let initialDescription = ''
  let initialFields: FieldRow[] = []

  if (isEdit && row) {
    initialTableName = row.name
    initialDescription = row.description ?? ''
    const option = tableOptions.find((o) => o.id === row.id)
    if (option) {
      initialFields = option.fields.map((f) => ({
        field_name: f.field_name,
        field_type: f.field_type,
        description: f.description ?? '',
        isOriginal: row.record_count > 0,
      }))
    }
  }

  return (
    <FnCustomTableFormInner
      key={row?.id ?? 'new'}
      open={open}
      row={row}
      onClose={onClose}
      onSuccess={onSuccess}
      initialTableName={initialTableName}
      initialDescription={initialDescription}
      initialFields={initialFields}
    />
  )
}
