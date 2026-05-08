import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import TextField from '@mui/material/TextField'
import MenuItem from '@mui/material/MenuItem'
import Chip from '@mui/material/Chip'
import Card from '@mui/material/Card'
import CardHeader from '@mui/material/CardHeader'
import CardContent from '@mui/material/CardContent'
import Tabs from '@mui/material/Tabs'
import Tab from '@mui/material/Tab'
import Collapse from '@mui/material/Collapse'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import ArrowBackIosNew from '@mui/icons-material/ArrowBackIosNew'
import InfoOutlined from '@mui/icons-material/InfoOutlined'
import CheckCircleOutline from '@mui/icons-material/CheckCircleOutline'
import ChatOutlined from '@mui/icons-material/ChatOutlined'
import SearchOutlined from '@mui/icons-material/SearchOutlined'
import DescriptionOutlined from '@mui/icons-material/DescriptionOutlined'
import HistoryOutlined from '@mui/icons-material/HistoryOutlined'
import SmartToyOutlined from '@mui/icons-material/SmartToyOutlined'
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import './IssueDetail.css'

const STATUS_LABEL: Record<string, string> = {
  pending: '未處理',
  investigating: '處理中',
  resolved: '已處理',
  dismissed: '擱置',
}
const STATUS_OPTIONS = Object.entries(STATUS_LABEL)

interface LogObject {
  id?: number | string
  timestamp?: number
  host?: string
  program?: string
  message: string
}

interface HistoryEntry {
  id: number | string
  created_at: string
  action: string
  old_status?: string
  new_status?: string
  note?: string
}

interface EventDetail {
  id: number | string
  title: string
  description?: string
  current_status: string
  assignee_user_id?: number | null
  affected_detail?: string
  suggests?: string[]
  mitre_tags?: string[]
  logs?: (string | LogObject)[]
  history?: HistoryEntry[]
}

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('mp-box-token')
  return token
    ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' }
}

function nowDT() {
  return new Date().toISOString().slice(0, 16)
}

function StatusIcon({ status, size = 14 }: { status: string; size?: number }) {
  if (status === 'pending')
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="#ef4444"
        strokeWidth="2"
      >
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    )
  if (status === 'investigating')
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="#f59e0b"
        strokeWidth="2"
      >
        <polyline points="23 4 23 10 17 10" />
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
      </svg>
    )
  if (status === 'resolved')
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="#10b981"
        strokeWidth="2"
      >
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    )
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="#94a3b8"
      strokeWidth="2"
    >
      <rect x="6" y="4" width="4" height="16" />
      <rect x="14" y="4" width="4" height="16" />
    </svg>
  )
}

function formatDesc(text?: string | null) {
  if (!text) return null
  return text.split(/(?=【)/).map((seg, i) => {
    if (!seg) return null
    const m = seg.match(/^【([^\]】]+)】([\s\S]*)$/)
    if (m)
      return (
        <Box key={i} sx={{ mb: 1.5 }}>
          <Typography
            sx={{
              fontWeight: 800,
              fontSize: 13,
              color: '#1e293b',
              mb: 0.5,
              letterSpacing: 0.3,
            }}
          >
            【{m[1]}】
          </Typography>
          <Typography
            sx={{
              pl: 1.75,
              borderLeft: '2px solid #e2e8f0',
              color: '#334155',
              fontSize: 13,
              lineHeight: 1.75,
              whiteSpace: 'pre-wrap',
            }}
          >
            {m[2].trim()}
          </Typography>
        </Box>
      )
    return (
      <Typography
        key={i}
        sx={{
          fontSize: 13,
          color: '#334155',
          lineHeight: 1.75,
          mb: 1,
          whiteSpace: 'pre-wrap',
        }}
      >
        {seg.trim()}
      </Typography>
    )
  })
}

export default function IssueDetail() {
  const { issueId } = useParams()
  const navigate = useNavigate()

  const [event, setEvent] = useState<EventDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tabIndex, setTabIndex] = useState(0)
  const [chatVisible, setChatVisible] = useState(true)

  const [histDate, setHistDate] = useState(nowDT)
  const [histNote, setHistNote] = useState('')
  const [histStatus, setHistStatus] = useState('')

  const fetchEvent = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/api/events/${issueId}`, {
        headers: authHeaders(),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data: EventDetail = await res.json()
      setEvent(data)
      setHistStatus(data.current_status)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [issueId])

  useEffect(() => {
    fetchEvent()
  }, [fetchEvent])
  useEffect(() => {
    setTabIndex(0)
    setChatVisible(true)
  }, [issueId])

  if (loading)
    return (
      <Box className="issue-detail-loading">
        <CircularProgress size={32} />
      </Box>
    )
  if (error || !event)
    return (
      <Box className="issue-detail-error">
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || '找不到此事件'}
        </Alert>
        <Button onClick={() => navigate(-1)} className="issue-detail-back-link">
          ← 返回
        </Button>
      </Box>
    )

  async function updateStatus(newStatus: string) {
    try {
      const res = await fetch(`/api/events/${issueId}`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify({ current_status: newStatus }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchEvent()
    } catch (e) {
      alert(`更新失敗: ${e instanceof Error ? e.message : String(e)}`)
    }
  }

  async function addHistoryEntry() {
    if (!histNote.trim()) {
      alert('請輸入備註內容')
      return
    }
    if (event && histStatus !== event.current_status) await updateStatus(histStatus)
    try {
      const res = await fetch(`/api/events/${issueId}/history`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          note: histNote,
          resolved_at: histStatus === 'resolved' ? new Date(histDate).toISOString() : null,
        }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setHistNote('')
      setHistDate(nowDT())
      await fetchEvent()
    } catch (e) {
      alert(`新增失敗: ${e instanceof Error ? e.message : String(e)}`)
    }
  }

  return (
    <Box className="issue-detail-root">
      <Box className="issue-detail-header">
        <Typography className="issue-detail-title">{event.title}</Typography>
        <Box className="issue-detail-meta-group">
          <Box className="issue-detail-meta-item">
            <Typography className="issue-detail-meta-label">處理狀態:</Typography>
            <Box className="issue-detail-meta-pill">
              <StatusIcon status={event.current_status} />
              <Typography className="issue-detail-meta-pill-text">
                {STATUS_LABEL[event.current_status]}
              </Typography>
            </Box>
          </Box>
          <Box className="issue-detail-meta-item">
            <Typography className="issue-detail-meta-label">負責人員:</Typography>
            <Typography className="issue-detail-assignee-pill">
              {event.assignee_user_id ? `User #${event.assignee_user_id}` : '未指派'}
            </Typography>
          </Box>
          <Button
            onClick={() => navigate(`/fn_expert`)}
            variant="outlined"
            startIcon={<ArrowBackIosNew sx={{ fontSize: '14px !important' }} />}
            className="issue-detail-back-btn"
          >
            回上一頁
          </Button>
        </Box>
      </Box>

      <Box className="issue-detail-body">
        <Box className="issue-detail-main">
          <Tabs
            value={tabIndex}
            onChange={(_, v) => setTabIndex(v)}
            className="issue-detail-tabs-bar"
            sx={{
              '& .MuiTab-root': {
                minHeight: 42,
                fontSize: 13,
                fontWeight: 600,
                textTransform: 'none',
                color: '#64748b',
                gap: 0.75,
              },
              '& .Mui-selected': { color: '#2e3f6e !important' },
              '& .MuiTabs-indicator': { bgcolor: '#2e3f6e' },
            }}
          >
            <Tab
              icon={<InfoOutlined sx={{ fontSize: 16 }} />}
              iconPosition="start"
              label="事件詳情"
            />
            <Tab
              icon={<SearchOutlined sx={{ fontSize: 16 }} />}
              iconPosition="start"
              label="歷史事件"
            />
            <Tab
              icon={<DescriptionOutlined sx={{ fontSize: 16 }} />}
              iconPosition="start"
              label="處置紀錄"
            />
          </Tabs>

          <Box className="issue-detail-tabs-panel">
            {tabIndex === 0 && (
              <>
                <Card variant="outlined" className="issue-detail-card-mb">
                  <CardHeader
                    avatar={<InfoOutlined sx={{ color: '#2e3f6e' }} />}
                    title="事件摘要"
                    titleTypographyProps={{
                      fontWeight: 700,
                      fontSize: 15,
                      color: '#1e293b',
                    }}
                    className="issue-detail-card-header"
                  />
                  <CardContent>
                    {event.description && (
                      <Typography className="issue-detail-summary-text">
                        {event.description}
                      </Typography>
                    )}
                    {formatDesc(event.affected_detail)}
                  </CardContent>
                </Card>

                {event.suggests && event.suggests.length > 0 && (
                  <Card variant="outlined" className="issue-detail-card-mb">
                    <CardHeader
                      avatar={<CheckCircleOutline sx={{ color: '#94a3b8' }} />}
                      title="建議處置方法"
                      titleTypographyProps={{
                        fontWeight: 700,
                        fontSize: 15,
                        color: '#1e293b',
                      }}
                      className="issue-detail-card-header"
                    />
                    <CardContent sx={{ py: 1 }}>
                      <List dense disablePadding>
                        {event.suggests.map((s, idx) => {
                          const urgency = idx < 2 ? '最推薦' : idx < 4 ? '次推薦' : '可選'
                          const urgencyStyleMap: Record<string, Record<string, string>> = {
                            最推薦: {
                              bgcolor: '#eef1f8',
                              color: '#2e3f6e',
                              border: '1px solid #c5ccdf',
                            },
                            次推薦: {
                              bgcolor: '#f8fafc',
                              color: '#475569',
                              border: '1px solid #cbd5e1',
                            },
                            可選: {
                              bgcolor: '#f8fafc',
                              color: '#94a3b8',
                              border: '1px solid #e2e8f0',
                            },
                          }
                          const urgencyStyle = urgencyStyleMap[urgency]
                          const mitreTag =
                            event.mitre_tags && event.mitre_tags[idx % event.mitre_tags.length]
                          return (
                            <ListItem key={idx} className="issue-detail-history-list-item">
                              <Chip
                                label={urgency}
                                size="small"
                                sx={{
                                  mr: 1.5,
                                  mt: 0.25,
                                  fontSize: 11,
                                  fontWeight: 700,
                                  borderRadius: 1,
                                  minWidth: 52,
                                  height: 22,
                                  ...urgencyStyle,
                                }}
                              />
                              <ListItemText
                                primary={s}
                                primaryTypographyProps={{
                                  fontSize: 14,
                                  color: '#334155',
                                  lineHeight: 1.7,
                                }}
                                sx={{ flex: 1 }}
                              />
                              {mitreTag && (
                                <Chip
                                  label={mitreTag}
                                  size="small"
                                  component="a"
                                  href={`https://attack.mitre.org/techniques/${mitreTag.replace('.', '/')}`}
                                  target="_blank"
                                  clickable
                                  icon={
                                    <svg
                                      width="10"
                                      height="10"
                                      viewBox="0 0 24 24"
                                      fill="none"
                                      stroke="currentColor"
                                      strokeWidth="2.5"
                                    >
                                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                                      <polyline points="15 3 21 3 21 9" />
                                      <line x1="10" y1="14" x2="21" y2="3" />
                                    </svg>
                                  }
                                  sx={{
                                    ml: 1,
                                    mt: 0.25,
                                    fontSize: 11,
                                    fontWeight: 700,
                                    fontFamily: 'monospace',
                                    bgcolor: '#f8f8f8',
                                    color: '#374151',
                                    border: '1px solid #d1d5db',
                                    flexShrink: 0,
                                    height: 22,
                                    '&:hover': {
                                      bgcolor: '#eef1f8',
                                      borderColor: '#2e3f6e',
                                    },
                                  }}
                                />
                              )}
                            </ListItem>
                          )
                        })}
                      </List>
                    </CardContent>
                  </Card>
                )}

                {event.logs && event.logs.length > 0 && (
                  <Card variant="outlined" className="issue-detail-card-mb">
                    <CardHeader
                      avatar={<ChatOutlined sx={{ color: '#475569' }} />}
                      title={`關聯日誌摘要（${event.logs.length} 筆）`}
                      titleTypographyProps={{
                        fontWeight: 700,
                        fontSize: 15,
                        color: '#1e293b',
                      }}
                      className="issue-detail-card-header"
                    />
                    <CardContent sx={{ bgcolor: '#f8fafc' }}>
                      {event.logs.map((log, i) => {
                        if (typeof log === 'string') {
                          return (
                            <Box key={i} className="issue-detail-log-string">
                              {log}
                            </Box>
                          )
                        }
                        const ts = log.timestamp
                          ? new Date(log.timestamp * 1000).toLocaleString('zh-TW')
                          : ''
                        return (
                          <Box key={i} className="issue-detail-log-card">
                            <Box className="issue-detail-log-meta">
                              {log.id && (
                                <Chip
                                  label={`SSB ID: ${log.id}`}
                                  size="small"
                                  className="issue-detail-log-meta-chip"
                                />
                              )}
                              {ts && <span>{ts}</span>}
                              {log.host && <span>Host: {log.host}</span>}
                              {log.program && <span>Program: {log.program}</span>}
                            </Box>
                            <Box className="issue-detail-log-body">{log.message}</Box>
                          </Box>
                        )
                      })}
                    </CardContent>
                  </Card>
                )}
              </>
            )}

            {tabIndex === 1 && (
              <Box>
                <Box className="issue-detail-tab-section-header">
                  <SearchOutlined sx={{ color: '#94a3b8', fontSize: 18 }} />
                  <Typography className="issue-detail-tab-section-title">歷史事件</Typography>
                </Box>
                <Typography className="issue-detail-tab-section-hint">
                  相似度由 PRO 模型依據事件描述語意、MITRE
                  技術重疊度、影響設備類型自動計算，於每日分析時寫入。
                </Typography>
                <Box className="issue-detail-empty">
                  <SearchOutlined className="issue-detail-empty-icon" />
                  <Typography className="issue-detail-empty-text">尚無相似歷史案例記錄</Typography>
                </Box>
              </Box>
            )}

            {tabIndex === 2 && (
              <Box>
                <Box className="issue-detail-tab-section-header issue-detail-tab-section-header-mb14">
                  <HistoryOutlined sx={{ color: '#94a3b8', fontSize: 18 }} />
                  <Typography className="issue-detail-tab-section-title">處置紀錄</Typography>
                  <Typography sx={{ fontSize: 11, color: '#94a3b8' }}>
                    — 記錄每次處理動作與備註
                  </Typography>
                </Box>

                <Box className="issue-detail-history-mb">
                  {!event.history || event.history.length === 0 ? (
                    <Typography className="issue-detail-history-empty">（尚無處置紀錄）</Typography>
                  ) : (
                    <List dense disablePadding>
                      {event.history.map((h) => (
                        <ListItem
                          key={h.id}
                          className="issue-detail-history-list-item issue-detail-history-list-item-pad0"
                        >
                          <ListItemText
                            primary={
                              <Box className="issue-detail-history-meta">
                                <Typography className="issue-detail-history-time">
                                  {new Date(h.created_at).toLocaleString('zh-TW')}
                                </Typography>
                                <Chip
                                  label={
                                    h.action === 'status_change'
                                      ? `${STATUS_LABEL[h.old_status || ''] || h.old_status} → ${STATUS_LABEL[h.new_status || ''] || h.new_status}`
                                      : h.action === 'assign'
                                        ? '指派變更'
                                        : h.action === 'resolve'
                                          ? '結案'
                                          : '留言'
                                  }
                                  size="small"
                                  className="issue-detail-history-chip"
                                />
                              </Box>
                            }
                            secondary={h.note}
                            secondaryTypographyProps={{
                              fontSize: 13,
                              color: '#334155',
                              mt: 0.5,
                            }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  )}
                </Box>

                <Card variant="outlined" className="issue-detail-history-form">
                  <CardContent
                    sx={{
                      display: 'flex',
                      gap: 1,
                      flexWrap: 'nowrap',
                      alignItems: 'flex-end',
                      '&:last-child': { pb: 2 },
                    }}
                  >
                    <Box>
                      <Typography className="issue-detail-history-form-label">日期</Typography>
                      <TextField
                        type="datetime-local"
                        value={histDate}
                        onChange={(e) => setHistDate(e.target.value)}
                        size="small"
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            height: 36,
                            fontSize: 13,
                            '& fieldset': { borderColor: '#cbd5e1' },
                          },
                          '& .MuiInputBase-input': { py: 0 },
                        }}
                      />
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Typography className="issue-detail-history-form-label">備註</Typography>
                      <TextField
                        value={histNote}
                        onChange={(e) => setHistNote(e.target.value)}
                        placeholder="輸入處理動作備註..."
                        size="small"
                        fullWidth
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            height: 36,
                            fontSize: 13,
                            '& fieldset': { borderColor: '#cbd5e1' },
                          },
                          '& .MuiInputBase-input': { py: 0 },
                        }}
                      />
                    </Box>
                    <Box>
                      <Typography className="issue-detail-history-form-label">變更狀態</Typography>
                      <TextField
                        select
                        value={histStatus}
                        onChange={(e) => setHistStatus(e.target.value)}
                        size="small"
                        sx={{
                          minWidth: 100,
                          '& .MuiOutlinedInput-root': {
                            height: 36,
                            fontSize: 13,
                            '& fieldset': { borderColor: '#cbd5e1' },
                          },
                          '& .MuiSelect-select': { py: 0 },
                        }}
                      >
                        {STATUS_OPTIONS.map(([val, label]) => (
                          <MenuItem key={val} value={val} sx={{ fontSize: 13 }}>
                            {label}
                          </MenuItem>
                        ))}
                      </TextField>
                    </Box>
                    <Button onClick={addHistoryEntry} className="issue-detail-history-add-btn">
                      新增
                    </Button>
                  </CardContent>
                </Card>
              </Box>
            )}
          </Box>
        </Box>

        <Box
          className={`issue-detail-chat-col ${
            chatVisible ? 'issue-detail-chat-col-expanded' : 'issue-detail-chat-col-collapsed'
          }`}
        >
          <Box className="issue-detail-chat-header">
            {chatVisible && (
              <Typography className="issue-detail-chat-title">
                <SmartToyOutlined sx={{ fontSize: 18, color: '#2e3f6e' }} />
                諮詢資安專家
              </Typography>
            )}
            <IconButton
              onClick={() => setChatVisible((v) => !v)}
              title={chatVisible ? '收合' : '展開'}
              className="issue-detail-chat-toggle"
              sx={{ ml: chatVisible ? 0 : 'auto' }}
            >
              {chatVisible ? (
                <ChevronRightIcon sx={{ fontSize: 18, color: '#2e3f6e' }} />
              ) : (
                <ChevronLeftIcon sx={{ fontSize: 18, color: '#2e3f6e' }} />
              )}
            </IconButton>
          </Box>

          <Collapse in={chatVisible} orientation="horizontal" sx={{ flex: 1, minHeight: 0 }}>
            <Card variant="outlined" className="issue-detail-chat-card">
              <CardContent className="issue-detail-chat-empty">
                <SmartToyOutlined sx={{ fontSize: 48, color: '#cbd5e1', mb: 1.5 }} />
                <Typography className="issue-detail-chat-empty-title">AI 諮詢功能</Typography>
                <Typography className="issue-detail-chat-empty-desc">
                  即將推出 — 可針對事件詢問詳細處理步驟、技術背景或風險評估
                </Typography>
              </CardContent>
            </Card>
          </Collapse>
        </Box>
      </Box>
    </Box>
  )
}
