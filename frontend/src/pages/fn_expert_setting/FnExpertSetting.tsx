// src/pages/fn_expert_setting/FnExpertSetting.tsx
import { useEffect, useRef, useState, useCallback } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import Button from '@mui/material/Button'
import Alert from '@mui/material/Alert'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'
import InputAdornment from '@mui/material/InputAdornment'
import IconButton from '@mui/material/IconButton'
import VisibilityIcon from '@mui/icons-material/Visibility'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import {
  useExpertSettingQuery,
  useSaveExpertSetting,
  useSsbTest,
} from '@/queries/useExpertSettingQuery'
import {
  useAnalysisStatusQuery,
  useTriggerLogFetch,
  type AnalysisStatusResponse,
} from '@/queries/useExpertAnalysisQuery'
import useAuthStore from '@/stores/authStore'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

// ── Datetime helpers ─────────────────────────────────────────────────────────

function todayStart(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T00:00`
}

function nowLocal(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ── Form state ────────────────────────────────────────────────────────────────

interface FormState {
  haikuEnabled: boolean
  haikuIntervalMinutes: number
  sonnetEnabled: boolean
  scheduleTime: string
  ssbHost: string
  ssbPort: number
  ssbLogspace: string
  ssbUsername: string
  ssbPassword: string
}

function buildInitialForm(data: {
  haiku_enabled: boolean
  haiku_interval_minutes: number
  sonnet_enabled: boolean
  schedule_time: string | null
  ssb_host: string | null
  ssb_port: number | null
  ssb_logspace: string | null
  ssb_username: string | null
  ssb_password: string | null
}): FormState {
  return {
    haikuEnabled: data.haiku_enabled,
    haikuIntervalMinutes: data.haiku_interval_minutes ?? 30,
    sonnetEnabled: data.sonnet_enabled,
    scheduleTime: data.schedule_time ?? '02:00',
    ssbHost: data.ssb_host ?? '',
    ssbPort: data.ssb_port ?? 443,
    ssbLogspace: data.ssb_logspace ?? '',
    ssbUsername: data.ssb_username ?? '',
    ssbPassword: '',
  }
}

const DEFAULT_FORM: FormState = {
  haikuEnabled: false,
  haikuIntervalMinutes: 30,
  sonnetEnabled: false,
  scheduleTime: '02:00',
  ssbHost: '',
  ssbPort: 443,
  ssbLogspace: '',
  ssbUsername: '',
  ssbPassword: '',
}

// ── Component ─────────────────────────────────────────────────────────────────

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

  // ── Log fetch (haiku) state & polling ──────────────────────────────────────

  const [logFetchFrom, setLogFetchFrom] = useState(todayStart())
  const [logFetchTo, setLogFetchTo] = useState(nowLocal())
  const [haikuStatus, setHaikuStatus] = useState<'idle' | 'running' | 'success' | 'failed'>('idle')
  const [recordsFetched, setRecordsFetched] = useState<number | null>(null)
  const [haikuError, setHaikuError] = useState<string | null>(null)
  const [haikuConflict, setHaikuConflict] = useState<string | null>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const isPollingRef = useRef(false)

  const { data: initialStatus } = useAnalysisStatusQuery()
  const triggerLogFetch = useTriggerLogFetch()

  const stopPolling = useCallback(() => {
    if (pollingRef.current !== null) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    isPollingRef.current = false
  }, [])

  async function fetchStatus(): Promise<AnalysisStatusResponse | null> {
    try {
      const token = useAuthStore.getState().token
      const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {}
      const res = await fetch(`${BASE_URL}/expert/analysis/status`, { headers })
      if (!res.ok) return null
      const json = await res.json()
      return (json.data ?? json) as AnalysisStatusResponse
    } catch {
      return null
    }
  }

  const pollHaiku = useCallback(() => {
    if (isPollingRef.current) return
    isPollingRef.current = true
    pollingRef.current = setInterval(async () => {
      const statusData = await fetchStatus()
      if (!statusData) return
      const s = statusData.haiku.status
      if (s === 'success' || s === 'failed') {
        stopPolling()
        setHaikuStatus(s)
        if (s === 'success') {
          setRecordsFetched(statusData.haiku.records_fetched ?? 0)
        } else {
          setHaikuError(statusData.haiku.error_message ?? '抓 log 失敗，請稍後重試')
        }
      } else {
        setHaikuStatus(s)
      }
    }, 3000)
  }, [stopPolling])

  useEffect(() => {
    if (!initialStatus) return
    const s = initialStatus.haiku.status
    setHaikuStatus(s)
    if (s === 'success') {
      setRecordsFetched(initialStatus.haiku.records_fetched ?? 0)
    } else if (s === 'failed') {
      setHaikuError(initialStatus.haiku.error_message ?? '抓 log 失敗，請稍後重試')
    } else if (s === 'running') {
      pollHaiku()
    }
  }, [initialStatus, pollHaiku])

  useEffect(() => {
    return () => stopPolling()
  }, [stopPolling])

  async function handleTriggerLogFetch() {
    setHaikuConflict(null)
    try {
      const fromISO = new Date(logFetchFrom).toISOString()
      const toISO = new Date(logFetchTo).toISOString()
      await triggerLogFetch.mutateAsync({ time_from: fromISO, time_to: toISO })
      setHaikuStatus('running')
      setRecordsFetched(null)
      setHaikuError(null)
      pollHaiku()
    } catch (err) {
      const e = err as Error & { status?: number }
      if (e.status === 409) {
        setHaikuConflict(e.message || '抓 log 進行中，請稍後再試')
      } else {
        setHaikuConflict(e.message || '抓取失敗')
      }
    }
  }

  // ── Handlers ──────────────────────────────────────────────────────────────

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
        haiku_enabled: currentForm.haikuEnabled,
        haiku_interval_minutes: currentForm.haikuIntervalMinutes,
        sonnet_enabled: currentForm.sonnetEnabled,
        schedule_time: currentForm.sonnetEnabled ? currentForm.scheduleTime : null,
        ssb_host: currentForm.ssbHost,
        ssb_port: currentForm.ssbPort,
        ssb_logspace: currentForm.ssbLogspace,
        ssb_username: currentForm.ssbUsername,
        ssb_password: currentForm.ssbPassword,
      })
      setSaveMessage('設定已儲存')
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : '儲存失敗')
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────

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

  return (
    <Box>
      {/* ── 兩欄排程區塊 ── */}
      <Box
        sx={{
          bgcolor: 'white',
          border: '1px solid #e2e8f0',
          borderRadius: 1,
          p: 2,
          mb: 2,
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 2,
        }}
      >
        {/* 左欄：定時抓取 log 資料 */}
        <Box>
          <Typography sx={{ fontSize: 16, fontWeight: 700, mb: 1.5, color: '#1e293b' }}>
            定時抓取 log 資料
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5, flexWrap: 'wrap' }}>
            <Switch
              checked={currentForm.haikuEnabled}
              onChange={(e) => updateForm({ haikuEnabled: e.target.checked })}
              color="success"
            />
            <Typography
              sx={{ fontSize: 13, color: currentForm.haikuEnabled ? '#16a34a' : '#64748b' }}
            >
              {currentForm.haikuEnabled ? '已開啟' : '啟用'}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 1 }}>
              <Typography sx={{ fontSize: 13, color: '#1e293b', whiteSpace: 'nowrap' }}>
                每
              </Typography>
              <TextField
                type="number"
                value={currentForm.haikuIntervalMinutes}
                onChange={(e) =>
                  updateForm({
                    haikuIntervalMinutes: Math.max(5, Math.min(1440, Number(e.target.value))),
                  })
                }
                inputProps={{ min: 5, max: 1440 }}
                size="small"
                sx={{ width: 80 }}
              />
              <Typography sx={{ fontSize: 13, color: '#1e293b', whiteSpace: 'nowrap' }}>
                分鐘
              </Typography>
            </Box>
          </Box>

          <Divider sx={{ mb: 1.5 }} />

          {/* 手動抓取 log 資料 */}
          <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#475569', mb: 1.5 }}>
            手動抓取 log 資料
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 1.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography sx={{ fontSize: 13, color: '#64748b', width: 36 }}>開始</Typography>
              <TextField
                type="datetime-local"
                value={logFetchFrom}
                onChange={(e) => setLogFetchFrom(e.target.value)}
                size="small"
                sx={{ flex: 1 }}
                inputProps={{ step: 60 }}
              />
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography sx={{ fontSize: 13, color: '#64748b', width: 36 }}>結束</Typography>
              <TextField
                type="datetime-local"
                value={logFetchTo}
                onChange={(e) => setLogFetchTo(e.target.value)}
                size="small"
                sx={{ flex: 1 }}
                inputProps={{ step: 60 }}
              />
            </Box>
          </Box>

          <Button
            variant="contained"
            size="small"
            disabled={haikuStatus === 'running'}
            onClick={handleTriggerLogFetch}
            startIcon={
              haikuStatus === 'running' ? <CircularProgress size={14} color="inherit" /> : undefined
            }
          >
            {haikuStatus === 'running' ? '抓取中…' : '立即抓取'}
          </Button>

          {haikuConflict && (
            <Typography sx={{ fontSize: 12, color: '#ef4444', mt: 0.5 }}>
              {haikuConflict}
            </Typography>
          )}
          {haikuStatus === 'success' && recordsFetched !== null && (
            <Typography sx={{ fontSize: 12, color: '#10b981', mt: 0.5 }}>
              抓取完成（{recordsFetched} 筆）
            </Typography>
          )}
          {haikuStatus === 'failed' && haikuError && (
            <Typography sx={{ fontSize: 12, color: '#ef4444', mt: 0.5 }}>{haikuError}</Typography>
          )}
        </Box>

        {/* 右欄：彙整並更新安全事件 */}
        <Box>
          <Typography sx={{ fontSize: 16, fontWeight: 700, mb: 1.5, color: '#1e293b' }}>
            彙整並更新安全事件
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
            <Switch
              checked={currentForm.sonnetEnabled}
              onChange={(e) => updateForm({ sonnetEnabled: e.target.checked })}
              color="success"
            />
            <Typography
              sx={{ fontSize: 13, color: currentForm.sonnetEnabled ? '#16a34a' : '#64748b' }}
            >
              {currentForm.sonnetEnabled ? '已開啟' : '啟用'}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 1 }}>
              <Typography sx={{ fontSize: 13, color: '#1e293b', whiteSpace: 'nowrap' }}>
                每日
              </Typography>
              <TextField
                type="time"
                value={currentForm.scheduleTime}
                onChange={(e) => updateForm({ scheduleTime: e.target.value })}
                size="small"
                sx={{ width: 150 }}
              />
            </Box>
          </Box>
        </Box>
      </Box>

      {/* ── SSB 連線設定區塊 ── */}
      <Box
        sx={{
          bgcolor: 'white',
          border: '1px solid #e2e8f0',
          borderRadius: 1,
          p: 2,
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
              placeholder={data?.ssb_password ? '已設定（留空保留原密碼）' : '密碼'}
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

      {/* ── 儲存按鈕 ── */}
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
          {saveExpertSetting.isPending ? (
            <CircularProgress size={18} color="inherit" />
          ) : (
            '儲存設定'
          )}
        </Button>
      </Box>
    </Box>
  )
}
