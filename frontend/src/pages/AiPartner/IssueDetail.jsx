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

// ── constants ──

const STATUS_LABEL = {
  pending: '未處理',
  investigating: '處理中',
  resolved: '已處理',
  dismissed: '擱置',
}
const STATUS_OPTIONS = Object.entries(STATUS_LABEL)

// ── helpers ──

function authHeaders() {
  const token = localStorage.getItem('mp-box-token')
  return token
    ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' }
}

function nowDT() {
  return new Date().toISOString().slice(0, 16)
}

function StatusIcon({ status, size = 14 }) {
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

function formatDesc(text) {
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

// ── Main ──

export default function IssueDetail() {
  const { partnerId, issueId } = useParams()
  const navigate = useNavigate()

  const [event, setEvent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [tabIndex, setTabIndex] = useState(0)
  const [chatVisible, setChatVisible] = useState(true)

  // history form
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
      const data = await res.json()
      setEvent(data)
      setHistStatus(data.current_status)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [issueId])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchEvent()
  }, [fetchEvent])
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTabIndex(0)
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setChatVisible(true)
  }, [issueId])

  if (loading)
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '50vh',
        }}
      >
        <CircularProgress size={32} />
      </Box>
    )
  if (error || !event)
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          py: 12,
        }}
      >
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || '找不到此事件'}
        </Alert>
        <Button onClick={() => navigate(-1)} sx={{ color: '#2e3f6e' }}>
          ← 返回
        </Button>
      </Box>
    )

  // ── actions ──

  async function updateStatus(newStatus) {
    try {
      const res = await fetch(`/api/events/${issueId}`, {
        method: 'PATCH',
        headers: authHeaders(),
        body: JSON.stringify({ current_status: newStatus }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchEvent()
    } catch (e) {
      alert(`更新失敗: ${e.message}`)
    }
  }

  async function addHistoryEntry() {
    if (!histNote.trim()) {
      alert('請輸入備註內容')
      return
    }
    if (histStatus !== event.current_status) await updateStatus(histStatus)
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
      alert(`新增失敗: ${e.message}`)
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 110px)',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
          flexShrink: 0,
        }}
      >
        <Typography sx={{ color: '#1e293b', fontSize: 18, fontWeight: 800 }}>
          {event.title}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography
              sx={{
                fontSize: 13,
                color: '#475569',
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              處理狀態:
            </Typography>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.75,
                px: 1.5,
                py: 0.75,
                border: '1.5px solid #e2e8f0',
                borderRadius: 1.5,
                bgcolor: '#f8fafc',
                minWidth: 100,
              }}
            >
              <StatusIcon status={event.current_status} />
              <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                {STATUS_LABEL[event.current_status]}
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography
              sx={{
                fontSize: 13,
                color: '#475569',
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              負責人員:
            </Typography>
            <Typography
              sx={{
                fontSize: 13,
                fontWeight: 600,
                color: '#1e293b',
                px: 1.5,
                py: 0.75,
                border: '1.5px solid #e2e8f0',
                borderRadius: 1.5,
                bgcolor: '#f8fafc',
                minWidth: 80,
              }}
            >
              {event.assignee_user_id ? `User #${event.assignee_user_id}` : '未指派'}
            </Typography>
          </Box>
          <Button
            onClick={() => navigate(`/ai-partner/${partnerId}/issues`)}
            variant="outlined"
            startIcon={<ArrowBackIosNew sx={{ fontSize: '14px !important' }} />}
            sx={{
              border: '1px solid #cbd5e1',
              bgcolor: 'white',
              borderRadius: 1,
              fontSize: 13.5,
              fontWeight: 600,
              color: '#334155',
              textTransform: 'none',
              '&:hover': { bgcolor: '#f8fafc' },
            }}
          >
            回上一頁
          </Button>
        </Box>
      </Box>

      {/* Two-column body */}
      <Box
        sx={{
          display: 'flex',
          gap: 2.5,
          flex: 1,
          overflow: 'hidden',
          minHeight: 0,
        }}
      >
        {/* Left: Tabs */}
        <Box
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            overflow: 'hidden',
          }}
        >
          <Tabs
            value={tabIndex}
            onChange={(_, v) => setTabIndex(v)}
            sx={{
              flexShrink: 0,
              bgcolor: 'white',
              borderRadius: '8px 8px 0 0',
              border: '1px solid #e2e8f0',
              borderBottom: 'none',
              minHeight: 42,
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

          {/* Tab panels */}
          <Box
            sx={{
              flex: 1,
              overflowY: 'auto',
              p: 2,
              bgcolor: 'white',
              border: '1px solid #e2e8f0',
              borderTop: 'none',
              borderRadius: '0 0 8px 8px',
              minHeight: 0,
            }}
          >
            {/* Tab 0: 事件詳情 */}
            {tabIndex === 0 && (
              <>
                <Card variant="outlined" sx={{ mb: 2 }}>
                  <CardHeader
                    avatar={<InfoOutlined sx={{ color: '#2e3f6e' }} />}
                    title="事件摘要"
                    titleTypographyProps={{
                      fontWeight: 700,
                      fontSize: 15,
                      color: '#1e293b',
                    }}
                    sx={{
                      bgcolor: '#f8fafc',
                      borderBottom: '1px solid #e2e8f0',
                      py: 1.5,
                    }}
                  />
                  <CardContent>
                    {event.description && (
                      <Typography
                        sx={{
                          fontSize: 14,
                          color: '#334155',
                          lineHeight: 1.75,
                          mb: 1.5,
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        {event.description}
                      </Typography>
                    )}
                    {formatDesc(event.affected_detail)}
                  </CardContent>
                </Card>

                {event.suggests && event.suggests.length > 0 && (
                  <Card variant="outlined" sx={{ mb: 2 }}>
                    <CardHeader
                      avatar={<CheckCircleOutline sx={{ color: '#94a3b8' }} />}
                      title="建議處置方法"
                      titleTypographyProps={{
                        fontWeight: 700,
                        fontSize: 15,
                        color: '#1e293b',
                      }}
                      sx={{
                        bgcolor: '#f8fafc',
                        borderBottom: '1px solid #e2e8f0',
                        py: 1.5,
                      }}
                    />
                    <CardContent sx={{ py: 1 }}>
                      <List dense disablePadding>
                        {event.suggests.map((s, idx) => {
                          const urgency = idx < 2 ? '最推薦' : idx < 4 ? '次推薦' : '可選'
                          const urgencyStyle = {
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
                          }[urgency]
                          // 從事件的 mitre_tags 裡對應溯源（依序分配）
                          const mitreTag =
                            event.mitre_tags && event.mitre_tags[idx % event.mitre_tags.length]
                          return (
                            <ListItem
                              key={idx}
                              sx={{
                                py: 1,
                                borderBottom: '1px solid #f1f5f9',
                                alignItems: 'flex-start',
                              }}
                            >
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
                  <Card variant="outlined" sx={{ mb: 2 }}>
                    <CardHeader
                      avatar={<ChatOutlined sx={{ color: '#475569' }} />}
                      title={`關聯日誌摘要（${event.logs.length} 筆）`}
                      titleTypographyProps={{
                        fontWeight: 700,
                        fontSize: 15,
                        color: '#1e293b',
                      }}
                      sx={{
                        bgcolor: '#f8fafc',
                        borderBottom: '1px solid #e2e8f0',
                        py: 1.5,
                      }}
                    />
                    <CardContent sx={{ bgcolor: '#f8fafc' }}>
                      {event.logs.map((log, i) => {
                        // log 可能是 string（舊格式）或 object（新格式，含 id/timestamp/host/message）
                        if (typeof log === 'string') {
                          return (
                            <Box
                              key={i}
                              sx={{
                                bgcolor: '#0f172a',
                                color: '#a5b4fc',
                                p: 1.5,
                                borderRadius: 1.5,
                                fontFamily: 'monospace',
                                fontSize: 13,
                                lineHeight: 1.5,
                                whiteSpace: 'pre-wrap',
                                mb: 0.625,
                              }}
                            >
                              {log}
                            </Box>
                          )
                        }
                        const ts = log.timestamp
                          ? new Date(log.timestamp * 1000).toLocaleString('zh-TW')
                          : ''
                        return (
                          <Box
                            key={i}
                            sx={{
                              bgcolor: '#0f172a',
                              borderRadius: 1.5,
                              mb: 0.75,
                              overflow: 'hidden',
                            }}
                          >
                            <Box
                              sx={{
                                display: 'flex',
                                gap: 1.5,
                                px: 1.5,
                                py: 0.75,
                                bgcolor: '#1e293b',
                                fontSize: 11,
                                color: '#94a3b8',
                                alignItems: 'center',
                                flexWrap: 'wrap',
                              }}
                            >
                              {log.id && (
                                <Chip
                                  label={`SSB ID: ${log.id}`}
                                  size="small"
                                  sx={{
                                    fontSize: 10,
                                    height: 18,
                                    bgcolor: '#334155',
                                    color: '#94a3b8',
                                    fontFamily: 'monospace',
                                  }}
                                />
                              )}
                              {ts && <span>{ts}</span>}
                              {log.host && <span>Host: {log.host}</span>}
                              {log.program && <span>Program: {log.program}</span>}
                            </Box>
                            <Box
                              sx={{
                                p: 1.5,
                                color: '#a5b4fc',
                                fontFamily: 'monospace',
                                fontSize: 13,
                                lineHeight: 1.5,
                                whiteSpace: 'pre-wrap',
                              }}
                            >
                              {log.message}
                            </Box>
                          </Box>
                        )
                      })}
                    </CardContent>
                  </Card>
                )}
              </>
            )}

            {/* Tab 1: 歷史事件（Epic 2） */}
            {tabIndex === 1 && (
              <Box>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 0.75,
                  }}
                >
                  <SearchOutlined sx={{ color: '#94a3b8', fontSize: 18 }} />
                  <Typography sx={{ fontSize: 14, fontWeight: 700, color: '#1e293b' }}>
                    歷史事件
                  </Typography>
                </Box>
                <Typography sx={{ fontSize: 11, color: '#94a3b8', mb: 1.75, pl: 3.25 }}>
                  相似度由 PRO 模型依據事件描述語意、MITRE
                  技術重疊度、影響設備類型自動計算，於每日分析時寫入。
                </Typography>
                <Box sx={{ textAlign: 'center', py: 4, color: '#94a3b8' }}>
                  <SearchOutlined sx={{ fontSize: 40, color: '#cbd5e1', mb: 1 }} />
                  <Typography sx={{ fontSize: 13 }}>尚無相似歷史案例記錄</Typography>
                </Box>
              </Box>
            )}

            {/* Tab 2: 處置紀錄 */}
            {tabIndex === 2 && (
              <Box>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 1.75,
                  }}
                >
                  <HistoryOutlined sx={{ color: '#94a3b8', fontSize: 18 }} />
                  <Typography sx={{ fontSize: 14, fontWeight: 700, color: '#1e293b' }}>
                    處置紀錄
                  </Typography>
                  <Typography sx={{ fontSize: 11, color: '#94a3b8' }}>
                    — 記錄每次處理動作與備註
                  </Typography>
                </Box>

                {/* History list */}
                <Box sx={{ mb: 1.75 }}>
                  {!event.history || event.history.length === 0 ? (
                    <Typography sx={{ fontSize: 13, color: '#94a3b8', py: 0.5 }}>
                      （尚無處置紀錄）
                    </Typography>
                  ) : (
                    <List dense disablePadding>
                      {event.history.map((h) => (
                        <ListItem
                          key={h.id}
                          sx={{
                            py: 1,
                            borderBottom: '1px solid #f1f5f9',
                            alignItems: 'flex-start',
                            px: 0,
                          }}
                        >
                          <ListItemText
                            primary={
                              <Box
                                sx={{
                                  display: 'flex',
                                  gap: 1.25,
                                  alignItems: 'center',
                                }}
                              >
                                <Typography
                                  sx={{
                                    fontSize: 11,
                                    color: '#94a3b8',
                                    whiteSpace: 'nowrap',
                                  }}
                                >
                                  {new Date(h.created_at).toLocaleString('zh-TW')}
                                </Typography>
                                <Chip
                                  label={
                                    h.action === 'status_change'
                                      ? `${STATUS_LABEL[h.old_status] || h.old_status} → ${STATUS_LABEL[h.new_status] || h.new_status}`
                                      : h.action === 'assign'
                                        ? '指派變更'
                                        : h.action === 'resolve'
                                          ? '結案'
                                          : '留言'
                                  }
                                  size="small"
                                  sx={{
                                    fontSize: 11,
                                    fontWeight: 600,
                                    bgcolor: '#eef1f8',
                                    color: '#2e3f6e',
                                    height: 22,
                                  }}
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

                {/* Add history form */}
                <Card variant="outlined" sx={{ bgcolor: '#f8fafc' }}>
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
                      <Typography sx={{ fontSize: 11, color: '#64748b', mb: 0.375 }}>
                        日期
                      </Typography>
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
                      <Typography sx={{ fontSize: 11, color: '#64748b', mb: 0.375 }}>
                        備註
                      </Typography>
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
                      <Typography sx={{ fontSize: 11, color: '#64748b', mb: 0.375 }}>
                        變更狀態
                      </Typography>
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
                    <Button
                      onClick={addHistoryEntry}
                      sx={{
                        height: 36,
                        px: 1.75,
                        bgcolor: '#2e3f6e',
                        color: 'white',
                        borderRadius: 1,
                        fontSize: 13,
                        fontWeight: 600,
                        textTransform: 'none',
                        '&:hover': { bgcolor: '#1e2d52' },
                      }}
                    >
                      新增
                    </Button>
                  </CardContent>
                </Card>
              </Box>
            )}
          </Box>
        </Box>

        {/* Right: Chat Panel */}
        <Box
          sx={{
            width: chatVisible ? 360 : 40,
            flexShrink: 0,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            overflow: 'hidden',
            transition: 'width 0.2s',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              mb: 1,
              flexShrink: 0,
            }}
          >
            {chatVisible && (
              <Typography
                sx={{
                  fontSize: 13,
                  fontWeight: 700,
                  color: '#1e293b',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 0.75,
                }}
              >
                <SmartToyOutlined sx={{ fontSize: 18, color: '#2e3f6e' }} />
                諮詢資安專家
              </Typography>
            )}
            <IconButton
              onClick={() => setChatVisible((v) => !v)}
              title={chatVisible ? '收合' : '展開'}
              sx={{
                width: 28,
                height: 28,
                borderRadius: 1,
                border: '1.5px solid #cbd5e1',
                bgcolor: 'white',
                flexShrink: 0,
                ml: chatVisible ? 0 : 'auto',
                '&:hover': { bgcolor: '#eef1f8', borderColor: '#2e3f6e' },
              }}
            >
              {chatVisible ? (
                <ChevronRightIcon sx={{ fontSize: 18, color: '#2e3f6e' }} />
              ) : (
                <ChevronLeftIcon sx={{ fontSize: 18, color: '#2e3f6e' }} />
              )}
            </IconButton>
          </Box>

          <Collapse in={chatVisible} orientation="horizontal" sx={{ flex: 1, minHeight: 0 }}>
            <Card
              variant="outlined"
              sx={{
                borderRadius: 3,
                display: 'flex',
                flexDirection: 'column',
                minHeight: 0,
                height: '100%',
              }}
            >
              <CardContent
                sx={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#94a3b8',
                }}
              >
                <SmartToyOutlined sx={{ fontSize: 48, color: '#cbd5e1', mb: 1.5 }} />
                <Typography
                  sx={{
                    fontSize: 14,
                    fontWeight: 600,
                    color: '#64748b',
                    mb: 0.5,
                  }}
                >
                  AI 諮詢功能
                </Typography>
                <Typography sx={{ fontSize: 12, color: '#94a3b8', textAlign: 'center' }}>
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
