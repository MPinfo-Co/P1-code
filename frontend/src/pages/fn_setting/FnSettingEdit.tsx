// src/pages/fn_setting/FnSettingEdit.tsx
import { useState } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import { useUpdateSetting } from '@/queries/useSettingsQuery'
import type { SettingRow } from '@/queries/useSettingsQuery'

interface Props {
  open: boolean
  row: SettingRow | null
  onClose: () => void
  onSuccess: () => void
}

function FnSettingEditInner({ open, row, onClose, onSuccess }: Props) {
  const [paramValue, setParamValue] = useState(row?.param_value ?? '')
  const [valueError, setValueError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const updateSetting = useUpdateSetting()

  function handleClose() {
    setValueError(null)
    setSubmitError(null)
    onClose()
  }

  async function handleSave() {
    if (!paramValue.trim()) {
      setValueError('參數值不可為空')
      return
    }
    setValueError(null)
    setSubmitError(null)
    try {
      await updateSetting.mutateAsync({
        paramCode: row!.param_code,
        payload: { param_value: paramValue.trim() },
      })
      onSuccess()
      onClose()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : '更新失敗，請稍後再試')
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ fontWeight: 800 }}>編輯參數值</DialogTitle>
      <DialogContent
        sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}
      >
        {submitError && (
          <Alert severity="error" sx={{ mb: 0 }}>
            {submitError}
          </Alert>
        )}
        <TextField
          label="參數類型"
          value={row?.param_type ?? ''}
          fullWidth
          size="small"
          InputProps={{ readOnly: true }}
        />
        <TextField
          label="參數代碼"
          value={row?.param_code ?? ''}
          fullWidth
          size="small"
          InputProps={{ readOnly: true }}
        />
        <TextField
          label="參數值"
          value={paramValue}
          onChange={(e) => {
            setParamValue(e.target.value)
            if (valueError) setValueError(null)
          }}
          fullWidth
          size="small"
          placeholder="請輸入參數值"
          error={!!valueError}
          helperText={valueError ?? undefined}
        />
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={handleClose} sx={{ color: '#64748b' }} disabled={updateSetting.isPending}>
          取消
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={updateSetting.isPending}
        >
          {updateSetting.isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default function FnSettingEdit(props: Props) {
  return <FnSettingEditInner key={props.row?.param_code ?? ''} {...props} />
}
