// src/pages/fn_expert_setting/FnExpertSetting.tsx
import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Switch from '@mui/material/Switch'
import FormControlLabel from '@mui/material/FormControlLabel'
import RadioGroup from '@mui/material/RadioGroup'
import Radio from '@mui/material/Radio'
import FormControl from '@mui/material/FormControl'
import TextField from '@mui/material/TextField'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import Button from '@mui/material/Button'
import Alert from '@mui/material/Alert'
import CircularProgress from '@mui/material/CircularProgress'
import InputAdornment from '@mui/material/InputAdornment'
import IconButton from '@mui/material/IconButton'
import VisibilityIcon from '@mui/icons-material/Visibility'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import {
  useExpertSettingQuery,
  useSaveExpertSetting,
  useSsbTest,
} from '@/queries/useExpertSettingQuery'

const MASKED_PASSWORD = '********'

interface FormState {
  isEnabled: boolean
  frequency: 'daily' | 'weekly' | 'manual'
  scheduleTime: string
  weekday: number
  ssbHost: string
  ssbPort: number
  ssbLogspace: string
  ssbUsername: string
  ssbPassword: string
}

function buildInitialForm(data: {
  is_enabled: boolean
  frequency: 'daily' | 'weekly' | 'manual'
  schedule_time: string | null
  weekday: number | null
  ssb_host: string | null
  ssb_port: number | null
  ssb_logspace: string | null
  ssb_username: string | null
  ssb_password: string | null
}): FormState {
  return {
    isEnabled: data.is_enabled,
    frequency: data.frequency ?? 'daily',
    scheduleTime: data.schedule_time ?? '02:00',
    weekday: data.weekday ?? 1,
    ssbHost: data.ssb_host ?? '',
    ssbPort: data.ssb_port ?? 443,
    ssbLogspace: data.ssb_logspace ?? '',
    ssbUsername: data.ssb_username ?? '',
    ssbPassword: data.ssb_password ? MASKED_PASSWORD : '',
  }
}

const DEFAULT_FORM: FormState = {
  isEnabled: false,
  frequency: 'daily',
  scheduleTime: '02:00',
  weekday: 1,
  ssbHost: '',
  ssbPort: 443,
  ssbLogspace: '',
  ssbUsername: '',
  ssbPassword: '',
}

export default function FnExpertSetting() {
  const { data, isLoading, error } = useExpertSettingQuery()

  const [form, setForm] = useState<FormState | null>(null)
  const [isPasswordVisible, setIsPasswordVisible] = useState(false)

  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [testMessage, setTestMessage] = useState<string | null>(null)
  const [testError, setTestError] = useState<string | null>(null)

  const saveExpertSetting = useSaveExpertSetting()
  const ssbTest = useSsbTest()

  // Initialize form from API data once loaded
  const currentForm: FormState = form ?? (data ? buildInitialForm(data) : DEFAULT_FORM)

  function updateForm(patch: Partial<FormState>) {
    setForm((prev) => ({ ...(prev ?? currentForm), ...patch }))
  }

  function handleTogglePasswordVisibility() {
    setIsPasswordVisible((prev) => !prev)
  }

  async function handleTestConnection() {
    setTestMessage(null)
    setTestError(null)
    try {
      await ssbTest.mutateAsync({
        host: currentForm.ssbHost,
        port: currentForm.ssbPort,
        logspace: currentForm.ssbLogspace,
        username: currentForm.ssbUsername,
        password: currentForm.ssbPassword || '**',
      })
      setTestMessage('連線成功')
    } catch (err) {
      setTestError(err instanceof Error ? err.message : '連線失敗')
    }
  }

  async function handleSave() {
    setSaveMessage(null)
    setSaveError(null)
    try {
      await saveExpertSetting.mutateAsync({
        is_enabled: currentForm.isEnabled,
        frequency: currentForm.frequency,
        schedule_time: currentForm.frequency !== 'manual' ? currentForm.scheduleTime : null,
        weekday: currentForm.frequency === 'weekly' ? currentForm.weekday : null,
        ssb_host: currentForm.ssbHost,
        ssb_port: currentForm.ssbPort,
        ssb_logspace: currentForm.ssbLogspace,
        ssb_username: currentForm.ssbUsername,
        ssb_password: currentForm.ssbPassword === MASKED_PASSWORD ? '' : currentForm.ssbPassword,
      })
      setSaveMessage('設定已儲存')
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : '儲存失敗')
    }
  }

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        載入失敗：{(error as Error).message}
      </Alert>
    )
  }

  const scheduleDisabled = !currentForm.isEnabled

  return (
    <Box sx={{ maxWidth: 720, mx: 'auto' }}>
      {/* 分析排程區塊 */}
      <Box
        sx={{
          bgcolor: 'white',
          border: '1px solid #e2e8f0',
          borderRadius: 1,
          p: 3,
          mb: 2,
        }}
      >
        <Typography sx={{ fontSize: 16, fontWeight: 700, mb: 2, color: '#1e293b' }}>
          分析排程
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
          <Typography sx={{ fontSize: 14, color: '#1e293b' }}>啟用排程</Typography>
          <Switch
            id="isEnabled"
            checked={currentForm.isEnabled}
            onChange={(e) => updateForm({ isEnabled: e.target.checked })}
            color="success"
          />
          <Typography
            sx={{
              fontSize: 13,
              color: currentForm.isEnabled ? '#16a34a' : '#64748b',
            }}
          >
            {currentForm.isEnabled ? '已開啟' : '已關閉'}
          </Typography>
        </Box>

        <Box
          sx={{
            opacity: scheduleDisabled ? 0.4 : 1,
            pointerEvents: scheduleDisabled ? 'none' : 'auto',
          }}
        >
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2 }}>
            <Box>
              <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b', mb: 0.5 }}>
                觸發時間
              </Typography>
              <TextField
                type="time"
                value={currentForm.scheduleTime}
                onChange={(e) => updateForm({ scheduleTime: e.target.value })}
                disabled={currentForm.frequency === 'manual'}
                size="small"
                inputProps={{ step: 60 }}
                sx={{ width: '100%' }}
              />
            </Box>
            <Box>
              <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b', mb: 0.5 }}>
                觸發頻率
              </Typography>
              <FormControl component="fieldset">
                <RadioGroup
                  row
                  value={currentForm.frequency}
                  onChange={(e) =>
                    updateForm({ frequency: e.target.value as 'daily' | 'weekly' | 'manual' })
                  }
                >
                  <FormControlLabel value="daily" control={<Radio size="small" />} label="每日" />
                  <FormControlLabel value="weekly" control={<Radio size="small" />} label="每週" />
                  <FormControlLabel value="manual" control={<Radio size="small" />} label="手動" />
                </RadioGroup>
              </FormControl>
            </Box>
          </Box>

          {currentForm.frequency === 'weekly' && (
            <Box sx={{ mb: 2 }}>
              <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b', mb: 0.5 }}>
                星期幾
              </Typography>
              <Select
                value={currentForm.weekday}
                onChange={(e) => updateForm({ weekday: Number(e.target.value) })}
                size="small"
                sx={{ minWidth: 160 }}
              >
                <MenuItem value={1}>週一</MenuItem>
                <MenuItem value={2}>週二</MenuItem>
                <MenuItem value={3}>週三</MenuItem>
                <MenuItem value={4}>週四</MenuItem>
                <MenuItem value={5}>週五</MenuItem>
                <MenuItem value={6}>週六</MenuItem>
                <MenuItem value={0}>週日</MenuItem>
              </Select>
            </Box>
          )}

          {currentForm.frequency === 'manual' && (
            <Typography sx={{ fontSize: 13, color: '#64748b', mt: 1 }}>
              手動模式不會自動執行；請至「資安專家」頁手動觸發分析。
            </Typography>
          )}
        </Box>
      </Box>

      {/* 資料來源區塊 */}
      <Box
        sx={{
          bgcolor: 'white',
          border: '1px solid #e2e8f0',
          borderRadius: 1,
          p: 3,
          mb: 2,
        }}
      >
        <Typography sx={{ fontSize: 16, fontWeight: 700, mb: 2, color: '#1e293b' }}>
          資料來源（syslog-ng Store Box）
        </Typography>

        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
          <Box>
            <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b', mb: 0.5 }}>
              Host
            </Typography>
            <TextField
              value={currentForm.ssbHost}
              onChange={(e) => updateForm({ ssbHost: e.target.value })}
              placeholder="192.168.10.48"
              size="small"
              fullWidth
            />
          </Box>
          <Box>
            <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b', mb: 0.5 }}>
              Port
            </Typography>
            <TextField
              type="number"
              value={currentForm.ssbPort}
              onChange={(e) => updateForm({ ssbPort: Number(e.target.value) })}
              inputProps={{ min: 1, max: 65535 }}
              size="small"
              fullWidth
            />
          </Box>
          <Box sx={{ gridColumn: '1 / -1' }}>
            <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b', mb: 0.5 }}>
              Logspace
            </Typography>
            <TextField
              value={currentForm.ssbLogspace}
              onChange={(e) => updateForm({ ssbLogspace: e.target.value })}
              placeholder="logspace 名稱"
              size="small"
              fullWidth
            />
          </Box>
          <Box>
            <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b', mb: 0.5 }}>
              Username
            </Typography>
            <TextField
              value={currentForm.ssbUsername}
              onChange={(e) => updateForm({ ssbUsername: e.target.value })}
              placeholder="帳號"
              size="small"
              fullWidth
            />
          </Box>
          <Box>
            <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b', mb: 0.5 }}>
              Password
            </Typography>
            <TextField
              type={isPasswordVisible ? 'text' : 'password'}
              value={currentForm.ssbPassword}
              onChange={(e) => updateForm({ ssbPassword: e.target.value })}
              placeholder="密碼"
              size="small"
              fullWidth
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={handleTogglePasswordVisibility} edge="end" size="small">
                      {isPasswordVisible ? (
                        <VisibilityOffIcon fontSize="small" />
                      ) : (
                        <VisibilityIcon fontSize="small" />
                      )}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        </Box>

        <Box
          sx={{
            display: 'flex',
            justifyContent: 'flex-end',
            mt: 2,
            gap: 1,
            flexDirection: 'column',
            alignItems: 'flex-end',
          }}
        >
          {testMessage && (
            <Alert severity="success" sx={{ width: '100%' }}>
              {testMessage}
            </Alert>
          )}
          {testError && (
            <Alert severity="error" sx={{ width: '100%' }}>
              {testError}
            </Alert>
          )}
          <Button variant="outlined" onClick={handleTestConnection} disabled={ssbTest.isPending}>
            {ssbTest.isPending ? <CircularProgress size={18} color="inherit" /> : '測試連線'}
          </Button>
        </Box>
      </Box>

      {saveMessage && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {saveMessage}
        </Alert>
      )}
      {saveError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {saveError}
        </Alert>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleSave}
          disabled={saveExpertSetting.isPending}
        >
          {saveExpertSetting.isPending ? <CircularProgress size={18} color="inherit" /> : '儲存'}
        </Button>
      </Box>
    </Box>
  )
}
