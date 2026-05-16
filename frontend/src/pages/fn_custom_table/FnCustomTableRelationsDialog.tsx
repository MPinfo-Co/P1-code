// src/pages/fn_custom_table/FnCustomTableRelationsDialog.tsx
import { useState, useEffect } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import {
  useCustomTableOptionsWithFieldsQuery,
  useCustomTableRelationsQuery,
  useSaveCustomTableRelations,
} from '@/queries/useCustomTableQuery'
import type {
  CustomTableOptionWithFields,
  CustomTableRelation,
  RelationPayloadItem,
} from '@/queries/useCustomTableQuery'

interface Props {
  open: boolean
  onClose: () => void
}

interface PendingRelation {
  id?: number
  src_table_id: number | ''
  src_field: string
  dst_table_id: number | ''
  dst_field: string
}

function getFieldsForTable(
  tables: CustomTableOptionWithFields[],
  tableId: number | ''
): { field_name: string; field_type: string }[] {
  if (!tableId) return []
  return tables.find((t) => t.id === tableId)?.fields ?? []
}

export default function FnCustomTableRelationsDialog({ open, onClose }: Props) {
  const [pendingRels, setPendingRels] = useState<PendingRelation[]>([])
  const [formError, setFormError] = useState<string | null>(null)

  const { data: tables = [], isLoading: isTablesLoading } = useCustomTableOptionsWithFieldsQuery()

  const {
    data: savedRelations,
    isLoading: isRelationsLoading,
    error: relationsError,
  } = useCustomTableRelationsQuery(open)

  const saveRelations = useSaveCustomTableRelations()

  // Populate pending list from saved relations when dialog opens or relations load
  useEffect(() => {
    if (!open) return
    if (savedRelations) {
      setPendingRels(
        savedRelations.map((r: CustomTableRelation) => ({
          id: r.id,
          src_table_id: r.src_table_id,
          src_field: r.src_field,
          dst_table_id: r.dst_table_id,
          dst_field: r.dst_field,
        }))
      )
    }
  }, [open, savedRelations])

  function isDirty(): boolean {
    if (!savedRelations) return pendingRels.length > 0
    if (pendingRels.length !== savedRelations.length) return true
    return pendingRels.some((p, i) => {
      const s = savedRelations[i]
      return (
        p.src_table_id !== s.src_table_id ||
        p.src_field !== s.src_field ||
        p.dst_table_id !== s.dst_table_id ||
        p.dst_field !== s.dst_field
      )
    })
  }

  function handleClose() {
    if (isDirty()) {
      if (!window.confirm('尚有未儲存的異動，確定離開？')) return
    }
    onClose()
  }

  function handleAddRow() {
    setPendingRels((prev) => [
      ...prev,
      { src_table_id: '', src_field: '', dst_table_id: '', dst_field: '' },
    ])
  }

  function handleDeleteRow(index: number) {
    if (!window.confirm('確定要移除此關聯？')) return
    setPendingRels((prev) => prev.filter((_, i) => i !== index))
  }

  function handleSrcTableChange(index: number, tableId: number | '') {
    setPendingRels((prev) =>
      prev.map((r, i) => (i === index ? { ...r, src_table_id: tableId, src_field: '' } : r))
    )
  }

  function handleDstTableChange(index: number, tableId: number | '') {
    setPendingRels((prev) =>
      prev.map((r, i) => (i === index ? { ...r, dst_table_id: tableId, dst_field: '' } : r))
    )
  }

  function handleFieldChange(index: number, key: 'src_field' | 'dst_field', value: string) {
    setPendingRels((prev) => prev.map((r, i) => (i === index ? { ...r, [key]: value } : r)))
  }

  async function handleSave() {
    setFormError(null)

    // Validate: all four fields required
    for (let i = 0; i < pendingRels.length; i++) {
      const r = pendingRels[i]
      if (!r.src_table_id || !r.src_field || !r.dst_table_id || !r.dst_field) {
        setFormError(`第 ${i + 1} 列關聯尚有未選取的欄位，請完整填寫後再儲存`)
        return
      }
    }

    const payload: RelationPayloadItem[] = pendingRels.map((r) => ({
      src_table_id: r.src_table_id as number,
      src_field: r.src_field,
      dst_table_id: r.dst_table_id as number,
      dst_field: r.dst_field,
    }))

    try {
      await saveRelations.mutateAsync(payload)
      onClose()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '儲存失敗，請稍後再試')
    }
  }

  const isLoading = isTablesLoading || isRelationsLoading

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ fontSize: 16, fontWeight: 600 }}>資料表關係維護</DialogTitle>
      <DialogContent sx={{ pt: '12px !important' }}>
        <Typography sx={{ fontSize: 13, color: '#64748b', mb: 2 }}>
          定義資料表之間的欄位關聯，供 AI 夥伴進行跨表分析。
        </Typography>

        {formError && (
          <Alert severity="error" onClose={() => setFormError(null)} sx={{ mb: 2 }}>
            {formError}
          </Alert>
        )}

        {relationsError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            載入關聯失敗：{(relationsError as Error).message}
          </Alert>
        )}

        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Header row */}
            {pendingRels.length > 0 && (
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 24px 1fr 1fr 64px',
                  gap: 1,
                  mb: 1,
                  px: 0.5,
                }}
              >
                <Typography sx={{ fontSize: 12, color: '#94a3b8', fontWeight: 600 }}>
                  來源表
                </Typography>
                <Typography sx={{ fontSize: 12, color: '#94a3b8', fontWeight: 600 }}>
                  來源欄位
                </Typography>
                <Box />
                <Typography sx={{ fontSize: 12, color: '#94a3b8', fontWeight: 600 }}>
                  目標表
                </Typography>
                <Typography sx={{ fontSize: 12, color: '#94a3b8', fontWeight: 600 }}>
                  目標欄位
                </Typography>
                <Box />
              </Box>
            )}

            {/* Relation rows */}
            {pendingRels.length === 0 ? (
              <Typography sx={{ fontSize: 13, color: '#94a3b8', textAlign: 'center', py: 3 }}>
                尚無定義任何關聯
              </Typography>
            ) : (
              pendingRels.map((rel, idx) => {
                const srcFields = getFieldsForTable(tables, rel.src_table_id)
                const dstFields = getFieldsForTable(tables, rel.dst_table_id)
                return (
                  <Box
                    key={idx}
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr 24px 1fr 1fr 64px',
                      gap: 1,
                      alignItems: 'center',
                      mb: 1,
                    }}
                  >
                    {/* 來源表 */}
                    <Select
                      size="small"
                      displayEmpty
                      value={rel.src_table_id === '' ? '' : String(rel.src_table_id)}
                      onChange={(e) => {
                        const v = e.target.value
                        handleSrcTableChange(idx, v === '' ? '' : Number(v))
                      }}
                      sx={{ fontSize: 13, height: 32 }}
                    >
                      <MenuItem value="" sx={{ fontSize: 13, color: '#94a3b8' }}>
                        — 選擇資料表 —
                      </MenuItem>
                      {tables.map((t) => (
                        <MenuItem key={t.id} value={String(t.id)} sx={{ fontSize: 13 }}>
                          {t.name}
                        </MenuItem>
                      ))}
                    </Select>

                    {/* 來源欄位 */}
                    <Select
                      size="small"
                      displayEmpty
                      value={rel.src_field}
                      disabled={!rel.src_table_id}
                      onChange={(e) => handleFieldChange(idx, 'src_field', e.target.value)}
                      sx={{ fontSize: 13, height: 32 }}
                    >
                      <MenuItem value="" sx={{ fontSize: 13, color: '#94a3b8' }}>
                        — 選擇欄位 —
                      </MenuItem>
                      {srcFields.map((f) => (
                        <MenuItem key={f.field_name} value={f.field_name} sx={{ fontSize: 13 }}>
                          {f.field_name}
                        </MenuItem>
                      ))}
                    </Select>

                    {/* Arrow */}
                    <Typography sx={{ fontSize: 16, color: '#64748b', textAlign: 'center' }}>
                      →
                    </Typography>

                    {/* 目標表 */}
                    <Select
                      size="small"
                      displayEmpty
                      value={rel.dst_table_id === '' ? '' : String(rel.dst_table_id)}
                      onChange={(e) => {
                        const v = e.target.value
                        handleDstTableChange(idx, v === '' ? '' : Number(v))
                      }}
                      sx={{ fontSize: 13, height: 32 }}
                    >
                      <MenuItem value="" sx={{ fontSize: 13, color: '#94a3b8' }}>
                        — 選擇資料表 —
                      </MenuItem>
                      {tables.map((t) => (
                        <MenuItem key={t.id} value={String(t.id)} sx={{ fontSize: 13 }}>
                          {t.name}
                        </MenuItem>
                      ))}
                    </Select>

                    {/* 目標欄位 */}
                    <Select
                      size="small"
                      displayEmpty
                      value={rel.dst_field}
                      disabled={!rel.dst_table_id}
                      onChange={(e) => handleFieldChange(idx, 'dst_field', e.target.value)}
                      sx={{ fontSize: 13, height: 32 }}
                    >
                      <MenuItem value="" sx={{ fontSize: 13, color: '#94a3b8' }}>
                        — 選擇欄位 —
                      </MenuItem>
                      {dstFields.map((f) => (
                        <MenuItem key={f.field_name} value={f.field_name} sx={{ fontSize: 13 }}>
                          {f.field_name}
                        </MenuItem>
                      ))}
                    </Select>

                    {/* 刪除 */}
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() => handleDeleteRow(idx)}
                      sx={{ fontSize: 12, height: 32, minWidth: 0 }}
                    >
                      刪除
                    </Button>
                  </Box>
                )
              })
            )}

            <Button
              variant="outlined"
              size="small"
              onClick={handleAddRow}
              sx={{ mt: 1, fontSize: 12 }}
            >
              ＋ 新增關聯
            </Button>
          </>
        )}
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose} sx={{ fontSize: 13 }} disabled={saveRelations.isPending}>
          取消
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={saveRelations.isPending || isLoading}
        >
          {saveRelations.isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
