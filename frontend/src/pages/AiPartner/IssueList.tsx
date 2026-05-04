import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Pagination from '@mui/material/Pagination'
import Chip from '@mui/material/Chip'
import Popover from '@mui/material/Popover'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined'
import './IssueList.css'

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

interface EventRow {
  id: number | string
  title: string
  star_rank: number
  event_date: string
  date_end?: string
  detection_count?: number
  affected_summary: string
  affected_detail?: string
  current_status: string
  assignee_user_id?: number | null
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

export default function IssueList() {
  const { partnerId } = useParams()
  const navigate = useNavigate()

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

  const [rows, setRows] = useState<EventRow[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [popoverAnchor, setPopoverAnchor] = useState<HTMLElement | null>(null)
  const [popoverContent, setPopoverContent] = useState('')

  const fetchEvents = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
      if (applied.status === '_default') params.set('status', 'pending,investigating')
      else if (applied.status !== 'all') params.set('status', applied.status)
      if (applied.keyword) params.set('keyword', applied.keyword)
      if (applied.start) params.set('date_from', applied.start)
      if (applied.end) params.set('date_to', applied.end)

      const token = localStorage.getItem('mp-box-token')
      const res = await fetch(`/api/events?${params}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setRows(data.items)
      setTotal(data.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [applied, page])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchEvents()
  }, [fetchEvents])

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

  const totalPages = Math.ceil(total / pageSize)

  return (
    <Box className="issue-list-root">
      <Box className="issue-list-header">
        <Typography variant="h5" className="issue-list-title">
          安全事件清單
        </Typography>
        <Button
          variant="outlined"
          startIcon={<ArrowBackOutlinedIcon />}
          size="small"
          onClick={() => navigate('/fn_partner')}
          className="issue-list-back-btn"
        >
          回上一頁
        </Button>
      </Box>

      <Box className="issue-list-filter-bar">
        <FormControl size="small" className="issue-list-filter-status">
          <InputLabel>處理狀態</InputLabel>
          <Select
            value={filterStatus}
            label="處理狀態"
            onChange={(e) => setFilterStatus(e.target.value)}
          >
            <MenuItem value="all">全部</MenuItem>
            {Object.entries(STATUS_LABEL).map(([val, label]) => (
              <MenuItem key={val} value={val}>
                {label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Typography className="issue-list-filter-label">發生日期:</Typography>
        <TextField
          size="small"
          type="date"
          value={filterStart}
          onChange={(e) => setFilterStart(e.target.value)}
          InputLabelProps={{ shrink: true }}
          className="issue-list-date"
        />
        <Typography className="issue-list-filter-sep">至</Typography>
        <TextField
          size="small"
          type="date"
          value={filterEnd}
          onChange={(e) => setFilterEnd(e.target.value)}
          InputLabelProps={{ shrink: true }}
          className="issue-list-date"
        />
        <Typography className="issue-list-filter-label">關鍵字:</Typography>
        <TextField
          size="small"
          placeholder="搜尋事件說明..."
          value={filterKeyword}
          onChange={(e) => setFilterKeyword(e.target.value)}
          className="issue-list-keyword"
        />
        <Button variant="outlined" onClick={applyFilters} className="issue-list-apply-btn">
          套用
        </Button>
        <Button variant="text" onClick={resetFilters} className="issue-list-reset-btn">
          重設
        </Button>
      </Box>

      {error && (
        <Alert severity="error" className="issue-list-error">
          載入失敗：{error}
        </Alert>
      )}

      <Box className="issue-list-table-wrap">
        {loading && (
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
              {rows.length === 0 && !loading ? (
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
                      onClick={() => navigate(`/fn_partner/${partnerId}/issues/${row.id}`)}
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
                            navigate(`/fn_partner/${partnerId}/issues/${row.id}`)
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

        {totalPages > 1 && (
          <Box className="issue-list-pagination-wrap">
            <Pagination
              count={totalPages}
              page={page}
              onChange={(_, v) => setPage(v)}
              shape="rounded"
              sx={{
                '& .MuiPaginationItem-root': { fontSize: 14, fontWeight: 500 },
                '& .Mui-selected': {
                  bgcolor: '#2e3f6e !important',
                  color: 'white',
                },
              }}
            />
          </Box>
        )}
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
