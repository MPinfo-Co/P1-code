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
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import IconButton from '@mui/material/IconButton'
import Divider from '@mui/material/Divider'
import LockOutlinedIcon from '@mui/icons-material/LockOutlined'
import { useCreateCustomTable, useUpdateCustomTable } from '@/queries/useCustomTableQuery'
import type { CustomTableRow, CustomTableField } from '@/queries/useCustomTableQuery'
import './FnCustomTableForm.css'

interface Props {
  open: boolean
  row: CustomTableRow | null
  onClose: () => void
  onSuccess: () => void
}

type FieldType = 'string' | 'number'

interface EditableField extends CustomTableField {
  isLocked?: boolean
}

export default function FnCustomTableForm({ open, row, onClose, onSuccess }: Props) {
  const isEdit = !!row

  const [tableName, setTableName] = useState(() => row?.name ?? '')
  const [tableDescription, setTableDescription] = useState(() => row?.description ?? '')
  const [fields, setFields] = useState<EditableField[]>(() => {
    if (!row) return [{ field_name: '', field_type: 'string', description: '' }]
    return (row as CustomTableRow & { fields?: EditableField[] }).fields ?? []
  })

  const [formError, setFormError] = useState<string | null>(null)

  const createCustomTable = useCreateCustomTable()
  const updateCustomTable = useUpdateCustomTable()

  const isPending = createCustomTable.isPending || updateCustomTable.isPending

  function handleAddField() {
    setFields((prev) => [...prev, { field_name: '', field_type: 'string', description: '' }])
  }

  function handleRemoveField(index: number) {
    setFields((prev) => prev.filter((_, i) => i !== index))
  }

  function handleFieldChange(index: number, key: keyof EditableField, value: unknown) {
    setFields((prev) => prev.map((f, i) => (i === index ? { ...f, [key]: value } : f)))
  }

  async function handleSave() {
    setFormError(null)

    if (!tableName.trim()) {
      setFormError('請填寫表格名稱')
      return
    }

    const validFields = fields.filter((f) => f.field_name.trim())
    if (validFields.length === 0) {
      setFormError('至少須定義一個欄位')
      return
    }

    const hasEmptyName = fields.some((f) => !f.field_name.trim())
    if (hasEmptyName) {
      setFormError('欄位名稱不可為空')
      return
    }

    try {
      const payload = {
        name: tableName.trim(),
        description: tableDescription.trim(),
        fields: fields.map((f) => ({
          field_name: f.field_name,
          field_type: f.field_type,
          description: f.description ?? '',
        })),
      }

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
      <DialogTitle className="fn-custom-table-form-title">
        {isEdit ? '編輯自訂資料表' : '新增自訂資料表'}
      </DialogTitle>
      <DialogContent sx={{ pt: '16px !important' }}>
        <Box className="fn-custom-table-form-stack">
          {formError && (
            <Alert severity="error" onClose={() => setFormError(null)}>
              {formError}
            </Alert>
          )}

          {/* 基本資訊 */}
          <Typography className="fn-custom-table-form-section-title">基本資訊</Typography>

          <Box>
            <Typography className="fn-custom-table-form-label">
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
            <Typography className="fn-custom-table-form-label">說明</Typography>
            <TextField
              fullWidth
              size="small"
              multiline
              rows={3}
              value={tableDescription}
              onChange={(e) => setTableDescription(e.target.value)}
              placeholder="描述此資料表的用途"
              sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
            />
          </Box>

          <Divider />

          {/* 欄位定義 */}
          <Typography className="fn-custom-table-form-section-title">欄位定義</Typography>
          <Typography sx={{ fontSize: 12, color: '#64748b', mt: -1 }}>
            至少須定義一個欄位才可儲存
          </Typography>

          {fields.map((field, index) => (
            <Box key={index} className="fn-custom-table-field-row">
              {field.isLocked && (
                <LockOutlinedIcon sx={{ fontSize: 16, color: '#94a3b8' }} />
              )}
              <TextField
                size="small"
                placeholder="欄位名稱"
                value={field.field_name}
                onChange={(e) => handleFieldChange(index, 'field_name', e.target.value)}
                disabled={field.isLocked}
                sx={{ flex: 1, minWidth: 100, '& .MuiInputBase-input': { fontSize: 13 } }}
              />
              <Select
                size="small"
                value={field.field_type}
                onChange={(e) => handleFieldChange(index, 'field_type', e.target.value as FieldType)}
                disabled={field.isLocked}
                sx={{ minWidth: 100, fontSize: 13 }}
              >
                {(['string', 'number'] as FieldType[]).map((t) => (
                  <MenuItem key={t} value={t} sx={{ fontSize: 13 }}>
                    {t}
                  </MenuItem>
                ))}
              </Select>
              <TextField
                size="small"
                placeholder="欄位說明"
                value={field.description ?? ''}
                onChange={(e) => handleFieldChange(index, 'description', e.target.value)}
                sx={{ flex: 2, '& .MuiInputBase-input': { fontSize: 13 } }}
              />
              {!field.isLocked && (
                <IconButton
                  size="small"
                  onClick={() => handleRemoveField(index)}
                  aria-label="刪除欄位"
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
            sx={{ mt: 1, fontSize: 12 }}
          >
            ＋ 新增欄位
          </Button>
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} className="fn-custom-table-form-cancel-btn" disabled={isPending}>
          取消
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={isPending}
          className="fn-custom-table-form-save-btn"
        >
          {isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
