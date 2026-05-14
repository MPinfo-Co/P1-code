import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Chip from '@mui/material/Chip'
import Popover from '@mui/material/Popover'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import Pagination from '@/components/ui/Pagination'
import { useEventsQuery } from '@/queries/useEventsQuery'
import type { EventRow } from '@/queries/useEventsQuery'
import { useQueryClient } from '@tanstack/react-query'
import { useAnalysisStatusQuery, useTriggerAnalysis } from '@/queries/useExpertAnalysisQuery'
import type { AnalysisStatus, AnalysisStatusResponse } from '@/queries/useExpertAnalysisQuery'
import useAuthStore from '@/stores/authStore'
import './IssueList.css'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

const STAR_COLOR: Record<number, string> = {
  5: '#b91c1c',
  4: '#c2410c',
  3: '#b45309',
  2: '#1e40af',
  1: '#475569',
}

const STATUS_LABEL: Record<string, string> = {
  pending: '未處理',
  investigating: '處理中',
  resolved: '已處理',
  dismissed: '擱置',
}

const STATUS_ICON: Record<string, React.ReactElement> = {
  pending: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  investigating: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2">
      <polyline points="23 4 23 10 17 10" />
      <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
    </svg>
  ),
  resolved: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  ),
  dismissed: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
      <rect x="6" y="4" width="4" height="16" />
      <rect x="14" y="4" width="4" height="16" />
    </svg>
  ),
}

interface AppliedFilters {
  status: string
  keyword: string
  start: string
  end: string
}

function formatDetectionCount(count: number) {
  if (!count) return ''
  if (count >= 10000) return `發生 ${(count / 10000).toFixed(1)} 萬次`
  return `發生 ${count.toLocaleString()} 次`
}

function formatDesc(text: string | null) {
  if (!text) return null
  const segments = text.split(/(?=【)/)
  return segments.map((seg, i) => {
    if (!seg) return null
    const m = seg.match(/^【([^\]】]+)】([\s\S]*)$/)
    if (m) {
      return (
        <Box key={i} sx={{ mb: 1.5 }}>
          <Typography sx={{ fontWeight: 800, fontSize: 13, color: '#1e293b', mb: 0.5 }}>
            【{m[1]}】
          </Typography>
          <Typography
            sx={{
              pl: 1.5,
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
    }
    return (
      <Typography key={i} sx={{ fontSize: 13, color: '#334155', lineHeight: 1.75, mb: 1 }}>
        {seg.trim()}
      </Typography>
    )
  })
}

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

async function fetchAnalysisStatus(): Promise<AnalysisStatusResponse | null> {
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

export default function IssueList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const [filterStatus, setFilterStatus] = useState('all')
  const [filterKeyword, setFilterKeyword] = useState('')
  const [filterStart, setFilterStart] = useState('')
  const [filterEnd, setFilterEnd] = useState('')
  const [applied, setApplied] = useState<AppliedFilters>({
    status: '_default',
    keyword: '',
    start: '',
    end: '',
  })
  const [page, setPage] = useState(1)
  const pageSize = 10

  const [popoverAnchor, setPopoverAnchor] = useState<HTMLElement | null>(null)
  const [popoverContent, setPopoverContent] = useState('')

  // Analysis button state
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>('idle')
  const [eventsCreated, setEventsCreated] = useState<number | null>(null)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const [conflictMsg, setConflictMsg] = useState<string | null>(null)
  const [analysisFrom, setAnalysisFrom] = useState(todayStart())
  const [analysisTo, setAnalysisTo] = useState(nowLocal())
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const isPollingRef = useRef(false)

  const { data: initialStatus } = useAnalysisStatusQuery()
  const triggerMutation = useTriggerAnalysis()

  const stopPolling = useCallback(() => {
    if (pollingRef.current !== null) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
    isPollingRef.current = false
  }, [])

  const pollStatus = useCallback(() => {
    if (isPollingRef.current) return
    isPollingRef.current = true
    pollingRef.current = setInterval(async () => {
      const data = await fetchAnalysisStatus()
      if (!data) return
      const s = data.sonnet.status
      if (s === 'success' || s === 'failed') {
        stopPolling()
        setAnalysisStatus(s)
        if (s === 'success') {
          setEventsCreated(data.sonnet.events_created ?? 0)
          queryClient.invalidateQueries({ queryKey: ['events'] })
        } else {
          setAnalysisError(data.sonnet.error_message ?? '彙整失敗，請稍後重試')
        }
      } else {
        setAnalysisStatus(s)
      }
    }, 3000)
  }, [stopPolling, queryClient])

  // On page enter: restore UI state from status API
  useEffect(() => {
    if (!initialStatus) return
    const s = initialStatus.sonnet.status
    setAnalysisStatus(s)
    if (s === 'success') {
      setEventsCreated(initialStatus.sonnet.events_created ?? 0)
    } else if (s === 'failed') {
      setAnalysisError(initialStatus.sonnet.error_message ?? '彙整失敗，請稍後重試')
    } else if (s === 'running') {
      pollStatus()
    }
  }, [initialStatus, pollStatus])

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      stopPolling()
    }
  }, [stopPolling])

  async function handleTriggerAnalysis() {
    setConflictMsg(null)
    try {
      const fromISO = new Date(analysisFrom).toISOString()
      const toISO = new Date(analysisTo).toISOString()
      await triggerMutation.mutateAsync({ time_from: fromISO, time_to: toISO })
      setAnalysisStatus('running')
      setEventsCreated(null)
      setAnalysisError(null)
      pollStatus()
    } catch (err) {
      const e = err as Error & { status?: number }
      if (e.status === 409) {
        setConflictMsg(e.message || '彙整進行中，請稍後再試')
      }
    }
  }

  const eventsStatus =
    applied.status === '_default'
      ? 'pending,investigating'
      : applied.status === 'all'
        ? undefined
        : applied.status

  const { data, isLoading, error } = useEventsQuery({
    page,
    pageSize,
    status: eventsStatus,
    dateStart: applied.start || undefined,
    dateEnd: applied.end || undefined,
    keyword: applied.keyword || undefined,
  })

  const rows: EventRow[] = data?.items ?? []
  const totalPages = data?.total_pages ?? 1

  function applyFilters() {
    setPage(1)
    setApplied({
      status: filterStatus,
      keyword: filterKeyword,
      start: filterStart,
      end: filterEnd,
    })
  }

  function resetFilters() {
    setFilterStatus('all')
    setFilterKeyword('')
    setFilterStart('')
    setFilterEnd('')
    setPage(1)
    setApplied({ status: '_default', keyword: '', start: '', end: '' })
  }

  function handlePopoverOpen(e: React.MouseEvent<HTMLElement>, row: EventRow) {
    e.stopPropagation()
    setPopoverAnchor(e.currentTarget)
    setPopoverContent(row.affected_detail || row.affected_summary)
  }

  return (
    <Box className="issue-list-root">
      <Box className="issue-list-header">
        <Typography variant="h5" className="issue-list-title">
          安全事件清單
        </Typography>
      </Box>

      <Box className="issue-list-filter-bar">
        <Typography className="issue-list-filter-label">處理狀態:</Typography>
        <Select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          size="small"
          displayEmpty
          className="issue-list-filter-status"
          sx={{ height: 24, fontSize: 13, '& .MuiSelect-select': { py: '2px' } }}
        >
          <MenuItem value="all">全部</MenuItem>
          {Object.entries(STATUS_LABEL).map(([val, label]) => (
            <MenuItem key={val} value={val}>
              {label}
            </MenuItem>
          ))}
        </Select>
        <Typography className="issue-list-filter-label">發生日期:</Typography>
        <TextField
          size="small"
          type="date"
          value={filterStart}
          onChange={(e) => setFilterStart(e.target.value)}
          InputLabelProps={{ shrink: true }}
          className="issue-list-date"
          sx={{
            '& .MuiInputBase-root': { height: 24 },
            '& .MuiInputBase-input': { py: '2px', fontSize: 13 },
          }}
        />
        <Typography className="issue-list-filter-sep">至</Typography>
        <TextField
          size="small"
          type="date"
          value={filterEnd}
          onChange={(e) => setFilterEnd(e.target.value)}
          InputLabelProps={{ shrink: true }}
          className="issue-list-date"
          sx={{
            '& .MuiInputBase-root': { height: 24 },
            '& .MuiInputBase-input': { py: '2px', fontSize: 13 },
          }}
        />
        <Typography className="issue-list-filter-label">關鍵字:</Typography>
        <TextField
          size="small"
          placeholder="搜尋事件說明..."
          value={filterKeyword}
          onChange={(e) => setFilterKeyword(e.target.value)}
          className="issue-list-keyword"
          sx={{
            '& .MuiInputBase-root': { height: 24 },
            '& .MuiInputBase-input': { py: '2px', fontSize: 13 },
          }}
        />
        <Button
          variant="outlined"
          size="small"
          onClick={applyFilters}
          className="issue-list-apply-btn"
        >
          套用
        </Button>
        <Button variant="text" size="small" onClick={resetFilters} className="issue-list-reset-btn">
          重設
        </Button>

        {/* One-click analysis button */}
        <Box
          sx={{
            ml: 'auto',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: 0.5,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography sx={{ fontSize: 11, color: '#64748b' }}>彙整範圍</Typography>
            <TextField
              size="small"
              type="datetime-local"
              value={analysisFrom}
              onChange={(e) => setAnalysisFrom(e.target.value)}
              sx={{
                '& .MuiInputBase-root': { height: 28 },
                '& .MuiInputBase-input': { py: '4px', fontSize: 11, width: 130 },
              }}
            />
            <Typography sx={{ fontSize: 11 }}>~</Typography>
            <TextField
              size="small"
              type="datetime-local"
              value={analysisTo}
              onChange={(e) => setAnalysisTo(e.target.value)}
              sx={{
                '& .MuiInputBase-root': { height: 28 },
                '& .MuiInputBase-input': { py: '4px', fontSize: 11, width: 130 },
              }}
            />
            <Button
              variant="contained"
              size="small"
              disabled={analysisStatus === 'running'}
              onClick={handleTriggerAnalysis}
              className="issue-list-analysis-btn"
              startIcon={
                analysisStatus === 'running' ? (
                  <CircularProgress size={14} color="inherit" />
                ) : undefined
              }
            >
              {analysisStatus === 'running' ? '分析中…' : '一鍵分析'}
            </Button>
          </Box>
          {conflictMsg && (
            <Typography sx={{ fontSize: 12, color: '#ef4444' }}>{conflictMsg}</Typography>
          )}
          {analysisStatus === 'success' && eventsCreated !== null && (
            <Typography sx={{ fontSize: 12, color: '#10b981' }}>
              {eventsCreated > 0 ? `新增 ${eventsCreated} 筆事件` : '本次無新增事件'}
            </Typography>
          )}
          {analysisStatus === 'failed' && analysisError && (
            <Typography sx={{ fontSize: 12, color: '#ef4444' }}>{analysisError}</Typography>
          )}
        </Box>
      </Box>

      {error && (
        <Alert severity="error" className="issue-list-error">
          載入失敗：{(error as Error).message}
        </Alert>
      )}

      <Box className="issue-list-table-wrap">
        {isLoading && (
          <Box className="issue-list-loading">
            <CircularProgress size={32} />
          </Box>
        )}

        <TableContainer className="issue-list-table-container">
          <Table stickyHeader>
            <TableHead>
              <TableRow>
                {[
                  '事件說明',
                  '處理優先級',
                  '發生期間',
                  '影響範圍',
                  '處理狀態',
                  '負責人員',
                  '執行動作',
                ].map((label) => (
                  <TableCell key={label} className="issue-list-th">
                    {label}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.length === 0 && !isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="issue-list-empty-cell">
                    尚無安全事件
                  </TableCell>
                </TableRow>
              ) : (
                rows.map((row) => {
                  const starColor = STAR_COLOR[row.star_rank] || '#475569'
                  return (
                    <TableRow
                      key={row.id}
                      hover
                      onClick={() => navigate(`/expert/issues/${row.id}`)}
                      className="issue-list-row"
                    >
                      <TableCell className="issue-list-cell-title">{row.title}</TableCell>

                      <TableCell>
                        <Box className="issue-list-stars">
                          <span className="issue-list-stars-on" style={{ color: starColor }}>
                            {'★'.repeat(row.star_rank)}
                          </span>
                          <span className="issue-list-stars-off">
                            {'★'.repeat(5 - row.star_rank)}
                          </span>
                        </Box>
                      </TableCell>

                      <TableCell>
                        <Typography className="issue-list-period">
                          {row.date_end && row.date_end !== row.event_date
                            ? `${row.event_date} ~ ${row.date_end}`
                            : row.event_date}
                        </Typography>
                        {row.detection_count != null && row.detection_count > 0 && (
                          <Typography className="issue-list-detection">
                            {formatDetectionCount(row.detection_count)}
                          </Typography>
                        )}
                      </TableCell>

                      <TableCell>
                        <Chip
                          icon={
                            <svg
                              width="12"
                              height="12"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                            >
                              <rect x="2" y="3" width="20" height="14" rx="2" />
                              <path d="M8 21h8M12 17v4" />
                            </svg>
                          }
                          label={row.affected_summary}
                          size="small"
                          onClick={(e) => handlePopoverOpen(e, row)}
                          className="issue-list-affected-chip"
                          sx={{
                            '& .MuiChip-label': {
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                            },
                          }}
                        />
                      </TableCell>

                      <TableCell>
                        <Box className="issue-list-status">
                          {STATUS_ICON[row.current_status] || STATUS_ICON.dismissed}
                          {STATUS_LABEL[row.current_status] || row.current_status}
                        </Box>
                      </TableCell>

                      <TableCell className="issue-list-cell-default">
                        {row.assignee_user_id ? (
                          `User #${row.assignee_user_id}`
                        ) : (
                          <Typography component="span" className="issue-list-unassigned">
                            未指派
                          </Typography>
                        )}
                      </TableCell>

                      <TableCell>
                        <Button
                          size="small"
                          variant="contained"
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/expert/issues/${row.id}`)
                          }}
                          className="issue-list-action-btn"
                          sx={{ py: 0.5 }}
                        >
                          事件處理
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <Pagination
          page={page}
          pageSize={pageSize}
          total={data?.total ?? 0}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      </Box>

      <Popover
        open={Boolean(popoverAnchor)}
        anchorEl={popoverAnchor}
        onClose={() => setPopoverAnchor(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
        slotProps={{
          paper: {
            sx: {
              p: 2,
              maxWidth: 400,
              border: '1px solid #e2e8f0',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
            },
          },
        }}
      >
        <Typography className="issue-list-popover-title">完整影響範圍</Typography>
        {formatDesc(popoverContent)}
      </Popover>
    </Box>
  )
}
