// src/pages/fn_ai_partner_config/FnAiPartnerConfigForm.tsx
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
import Radio from '@mui/material/Radio'
import RadioGroup from '@mui/material/RadioGroup'
import FormControlLabel from '@mui/material/FormControlLabel'
import Checkbox from '@mui/material/Checkbox'
import Divider from '@mui/material/Divider'
import {
  useCreateAiPartner,
  useUpdateAiPartner,
  useToolOptionsQuery,
} from '@/queries/useAiPartnerConfigQuery'
import type { AiPartnerRow } from '@/queries/useAiPartnerConfigQuery'
import './FnAiPartnerConfigForm.css'

interface Props {
  open: boolean
  row: AiPartnerRow | null
  onClose: () => void
  onSuccess: () => void
}

export default function FnAiPartnerConfigForm({ open, row, onClose, onSuccess }: Props) {
  const isEdit = !!row

  const [name, setName] = useState(() => row?.name ?? '')
  const [description, setDescription] = useState(() => row?.description ?? '')
  const [roleDefinition, setRoleDefinition] = useState(() => row?.role_definition ?? '')
  const [behaviorLimit, setBehaviorLimit] = useState(() => row?.behavior_limit ?? '')
  const [selectedToolIds, setSelectedToolIds] = useState<number[]>(() => row?.tool_ids ?? [])
  const [isEnabled, setIsEnabled] = useState<boolean>(() => row?.is_enabled ?? true)
  const [formError, setFormError] = useState<string | null>(null)

  const { data: toolOptions = [], isLoading: isToolsLoading } = useToolOptionsQuery()
  const createPartner = useCreateAiPartner()
  const updatePartner = useUpdateAiPartner()

  const isPending = createPartner.isPending || updatePartner.isPending

  function handleToolToggle(toolId: number) {
    setSelectedToolIds((prev) =>
      prev.includes(toolId) ? prev.filter((id) => id !== toolId) : [...prev, toolId]
    )
  }

  function handleSelectAll() {
    if (selectedToolIds.length === toolOptions.length) {
      setSelectedToolIds([])
    } else {
      setSelectedToolIds(toolOptions.map((t) => t.id))
    }
  }

  async function handleSave() {
    setFormError(null)
    if (!name.trim()) {
      setFormError('夥伴名稱為必填')
      return
    }

    try {
      if (isEdit && row) {
        await updatePartner.mutateAsync({
          id: row.id,
          payload: {
            name: name.trim(),
            description: description.trim() || undefined,
            role_definition: roleDefinition.trim() || undefined,
            behavior_limit: behaviorLimit.trim() || undefined,
            tool_ids: selectedToolIds,
            is_enabled: isEnabled,
          },
        })
      } else {
        await createPartner.mutateAsync({
          name: name.trim(),
          description: description.trim() || undefined,
          role_definition: roleDefinition.trim() || undefined,
          behavior_limit: behaviorLimit.trim() || undefined,
          tool_ids: selectedToolIds,
        })
      }
      onSuccess()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : '操作失敗，請稍後再試')
    }
  }

  const allSelected = toolOptions.length > 0 && selectedToolIds.length === toolOptions.length

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle className="fn-ai-partner-config-form-title">
        {isEdit ? '編輯 AI 夥伴' : '新增 AI 夥伴'}
      </DialogTitle>
      <DialogContent sx={{ pt: '16px !important' }}>
        <Box className="fn-ai-partner-config-form-stack">
          {formError && (
            <Alert severity="error" onClose={() => setFormError(null)}>
              {formError}
            </Alert>
          )}

          {/* 基本資訊 */}
          <Typography className="fn-ai-partner-config-form-section-title">基本資訊</Typography>

          <Box>
            <Typography className="fn-ai-partner-config-form-label">
              夥伴名稱 <span style={{ color: '#ef4444' }}>*</span>
            </Typography>
            <TextField
              fullWidth
              size="small"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="請輸入夥伴名稱"
              sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
            />
          </Box>

          <Box>
            <Typography className="fn-ai-partner-config-form-label">描述</Typography>
            <TextField
              fullWidth
              size="small"
              multiline
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="描述此 AI 夥伴的用途"
              sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
            />
          </Box>

          <Divider />

          {/* AI 行為定義 */}
          <Typography className="fn-ai-partner-config-form-section-title">AI 行為定義</Typography>

          <Box>
            <Typography className="fn-ai-partner-config-form-label">角色定義</Typography>
            <TextField
              fullWidth
              size="small"
              multiline
              rows={3}
              value={roleDefinition}
              onChange={(e) => setRoleDefinition(e.target.value)}
              placeholder="定義此 AI 夥伴的角色與職責"
              sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
            />
          </Box>

          <Box>
            <Typography className="fn-ai-partner-config-form-label">行為限制</Typography>
            <TextField
              fullWidth
              size="small"
              multiline
              rows={3}
              value={behaviorLimit}
              onChange={(e) => setBehaviorLimit(e.target.value)}
              placeholder="設定此 AI 夥伴不應執行的行為"
              sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
            />
          </Box>

          <Divider />

          {/* 可用工具 */}
          <Typography className="fn-ai-partner-config-form-section-title">可用工具</Typography>

          {isToolsLoading ? (
            <CircularProgress size={20} />
          ) : toolOptions.length > 0 ? (
            <Box>
              <Box className="fn-ai-partner-config-tool-select-all">
                <Button
                  size="small"
                  variant="outlined"
                  onClick={handleSelectAll}
                  sx={{ fontSize: 12, height: 24, borderRadius: '3px' }}
                >
                  {allSelected ? '取消全選' : '全選'}
                </Button>
              </Box>
              <Box className="fn-ai-partner-config-tool-group">
                {toolOptions.map((tool) => (
                  <Box key={tool.id} className="fn-ai-partner-config-tool-item">
                    <Checkbox
                      size="small"
                      checked={selectedToolIds.includes(tool.id)}
                      onChange={() => handleToolToggle(tool.id)}
                      sx={{ p: 0 }}
                    />
                    <Box>
                      <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                        {tool.name}
                      </Typography>
                      {tool.description && (
                        <Typography sx={{ fontSize: 12, color: '#64748b' }}>
                          {tool.description}
                        </Typography>
                      )}
                    </Box>
                  </Box>
                ))}
              </Box>
            </Box>
          ) : (
            <Typography sx={{ fontSize: 13, color: '#94a3b8' }}>尚無可用工具</Typography>
          )}

          {/* 狀態（僅修改模式顯示） */}
          {isEdit && (
            <>
              <Divider />
              <Typography className="fn-ai-partner-config-form-section-title">狀態</Typography>
              <RadioGroup
                row
                value={isEnabled ? 'enabled' : 'disabled'}
                onChange={(e) => setIsEnabled(e.target.value === 'enabled')}
              >
                <FormControlLabel value="enabled" control={<Radio size="small" />} label="啟用" />
                <FormControlLabel value="disabled" control={<Radio size="small" />} label="停用" />
              </RadioGroup>
            </>
          )}
        </Box>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={onClose}
          className="fn-ai-partner-config-form-cancel-btn"
          disabled={isPending}
        >
          取消
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={isPending}
          className="fn-ai-partner-config-form-save-btn"
        >
          {isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
