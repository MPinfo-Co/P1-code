import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useIssues } from '../../contexts/IssuesContext'
import { DataGrid } from '@mui/x-data-grid'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Chip from '@mui/material/Chip'
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined'

const STAR_COLOR = { 5: '#b91c1c', 4: '#c2410c', 3: '#b45309', 2: '#1e40af', 1: '#475569' }

const STATUS_COLOR = {
  '未處理': { bgcolor: '#fef2f2', color: '#dc2626' },
  '處理中': { bgcolor: '#fffbeb', color: '#d97706' },
  '已完成': { bgcolor: '#f0fdf4', color: '#16a34a' },
  '擱置':   { bgcolor: '#f8fafc', color: '#94a3b8' },
}

export default function IssueList() {
  const { partnerId } = useParams()
  const navigate = useNavigate()
  const { issues } = useIssues()

  const [filterStatus, setFilterStatus] = useState('all')
  const [filterKeyword, setFilterKeyword] = useState('')
  const [filterStart, setFilterStart] = useState('')
  const [filterEnd, setFilterEnd] = useState('')
  const [applied, setApplied] = useState({ status: 'all', keyword: '', start: '', end: '' })

  function applyFilters() {
    setApplied({ status: filterStatus, keyword: filterKeyword, start: filterStart, end: filterEnd })
  }

  function resetFilters() {
    setFilterStatus('all'); setFilterKeyword(''); setFilterStart(''); setFilterEnd('')
    setApplied({ status: 'all', keyword: '', start: '', end: '' })
  }

  const partnerIssues = issues.filter(i => i.partnerId === partnerId)
  const filtered = partnerIssues.filter(i => {
    if (applied.status !== 'all' && i.currentStatus !== applied.status) return false
    if (applied.keyword) {
      const kw = applied.keyword.toLowerCase()
      const fields = [i.title, i.affected, i.currentStatus, i.date, i.desc, String(i.starRank)]
      if (!fields.some(f => (f || '').toLowerCase().includes(kw))) return false
    }
    if (applied.start && i.date < applied.start) return false
    if (applied.end && i.date > applied.end) return false
    return true
  }).sort((a, b) => b.starRank - a.starRank)

  function getAssignee(issue) {
    if (issue.history?.length > 0) return issue.history[issue.history.length - 1].user
    return '未指派'
  }

  const columns = [
    {
      field: 'title', headerName: '事件說明', flex: 2, minWidth: 180,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#334155', lineHeight: 1.4 }}>{value}</Typography>
      ),
    },
    {
      field: 'starRank', headerName: '優先級', width: 120,
      renderCell: ({ value }) => {
        const color = STAR_COLOR[value] || '#475569'
        return (
          <Box>
            <span style={{ color, fontSize: 14, letterSpacing: 1 }}>{'★'.repeat(value)}</span>
            <span style={{ color: '#e2e8f0', fontSize: 14, letterSpacing: 1 }}>{'★'.repeat(5 - value)}</span>
          </Box>
        )
      },
    },
    {
      field: 'date', headerName: '發生日期', width: 160,
      renderCell: ({ row }) => (
        <Typography sx={{ fontSize: 13, color: '#475569' }}>
          {row.dateEnd && row.dateEnd !== row.date ? `${row.date} ~ ${row.dateEnd}` : row.date}
        </Typography>
      ),
    },
    {
      field: 'affectedSummary', headerName: '影響範圍', width: 160,
      renderCell: ({ value }) => (
        <Chip label={value} size="small" sx={{ fontSize: 11, bgcolor: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0' }} />
      ),
    },
    {
      field: 'currentStatus', headerName: '處理狀態', width: 120,
      renderCell: ({ value }) => {
        const s = STATUS_COLOR[value] || STATUS_COLOR['擱置']
        return <Chip label={value} size="small" sx={{ fontSize: 11, fontWeight: 700, ...s }} />
      },
    },
    {
      field: 'assignee', headerName: '負責人員', width: 120,
      valueGetter: (_, row) => getAssignee(row),
    },
    {
      field: 'actions', headerName: '執行動作', width: 110, sortable: false,
      renderCell: ({ row }) => (
        <Button
          size="small"
          variant="contained"
          onClick={() => navigate(`/ai-partner/${partnerId}/issues/${row.id}`)}
          sx={{ fontSize: 12, py: 0.5 }}
        >
          事件處理
        </Button>
      ),
    },
  ]

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 110px)' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexShrink: 0 }}>
        <Typography variant="h6" sx={{ fontWeight: 800, color: '#1e293b' }}>安全事件清單</Typography>
        <Button variant="outlined" startIcon={<ArrowBackOutlinedIcon />} size="small"
          onClick={() => navigate('/ai-partner')}
          sx={{ color: '#64748b', borderColor: '#cbd5e1' }}>
          回上一頁
        </Button>
      </Box>

      {/* Filter bar */}
      <Box sx={{ bgcolor: 'white', borderRadius: 2, border: '1px solid #e2e8f0', p: 2, mb: 2, flexShrink: 0, display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>處理狀態</InputLabel>
          <Select value={filterStatus} label="處理狀態" onChange={e => setFilterStatus(e.target.value)}>
            <MenuItem value="all">全部</MenuItem>
            {['未處理', '處理中', '已完成', '擱置'].map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
          </Select>
        </FormControl>
        <TextField size="small" label="開始日期" type="date" value={filterStart}
          onChange={e => setFilterStart(e.target.value)} InputLabelProps={{ shrink: true }} />
        <TextField size="small" label="結束日期" type="date" value={filterEnd}
          onChange={e => setFilterEnd(e.target.value)} InputLabelProps={{ shrink: true }} />
        <TextField size="small" label="關鍵字" placeholder="搜尋事件說明..."
          value={filterKeyword} onChange={e => setFilterKeyword(e.target.value)} sx={{ width: 200 }} />
        <Button variant="outlined" onClick={applyFilters} sx={{ borderColor: '#2e3f6e', color: '#2e3f6e' }}>套用</Button>
        <Button variant="text" onClick={resetFilters} sx={{ color: '#64748b' }}>重設</Button>
      </Box>

      {/* DataGrid */}
      <Box sx={{ flex: 1, minHeight: 0, bgcolor: 'white', borderRadius: 2, border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        <DataGrid
          rows={filtered}
          columns={columns}
          pageSizeOptions={[10, 25]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          onRowClick={({ row }) => navigate(`/ai-partner/${partnerId}/issues/${row.id}`)}
          disableRowSelectionOnClick
          sx={{ border: 'none' }}
        />
      </Box>
    </Box>
  )
}
