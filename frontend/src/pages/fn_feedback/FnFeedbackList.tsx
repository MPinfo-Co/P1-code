// src/pages/fn_feedback/FnFeedbackList.tsx
import { useState } from 'react'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import Alert from '@mui/material/Alert'
import CircularProgress from '@mui/material/CircularProgress'
import StarIcon from '@mui/icons-material/Star'
import { useFeedbackListQuery } from '@/queries/useFeedbackQuery'
import type { FeedbackRow } from '@/queries/useFeedbackQuery'
import './FnFeedbackList.css'

interface AppliedFilter {
  rating?: number
}

function formatDate(value: string): string {
  if (!value) return ''
  const d = new Date(value)
  const yyyy = d.getFullYear()
  const MM = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const HH = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${yyyy}-${MM}-${dd} ${HH}:${mm}`
}

function renderStars(rating: number) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
      {[1, 2, 3, 4, 5].map((v) => (
        <StarIcon key={v} sx={{ fontSize: 16, color: v <= rating ? '#f59e0b' : '#e2e8f0' }} />
      ))}
    </Box>
  )
}

export default function FnFeedbackList() {
  const [filterRating, setFilterRating] = useState<string>('all')
  const [appliedFilter, setAppliedFilter] = useState<AppliedFilter>({})

  const { data: feedbacks = [], isLoading, error } = useFeedbackListQuery(appliedFilter)

  function handleApply() {
    const filter: AppliedFilter = {}
    if (filterRating !== 'all') {
      filter.rating = Number(filterRating)
    }
    setAppliedFilter(filter)
  }

  const columns: GridColDef<FeedbackRow>[] = [
    {
      field: 'user_name',
      headerName: '用戶名稱',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 700 }}>{value}</Typography>
      ),
    },
    {
      field: 'rating',
      headerName: '評分',
      width: 130,
      renderCell: ({ value }) => renderStars(value as number),
    },
    {
      field: 'comment_summary',
      headerName: '留言摘要',
      flex: 2,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#475569' }}>
          {value ? (value as string) : '—'}
        </Typography>
      ),
    },
    {
      field: 'created_at',
      headerName: '提交時間',
      width: 160,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#475569' }}>
          {formatDate(value as string)}
        </Typography>
      ),
    },
  ]

  return (
    <Box>
      {/* 篩選列 */}
      <Box className="fn-feedback-filter-bar">
        <Box className="fn-feedback-filter-group">
          <Typography className="fn-feedback-filter-label">評分:</Typography>
          <Select
            value={filterRating}
            onChange={(e) => setFilterRating(e.target.value)}
            size="small"
            displayEmpty
            sx={{ height: 24, fontSize: 13, '& .MuiSelect-select': { py: '2px' } }}
          >
            <MenuItem value="all">全部</MenuItem>
            <MenuItem value="1">1星</MenuItem>
            <MenuItem value="2">2星</MenuItem>
            <MenuItem value="3">3星</MenuItem>
            <MenuItem value="4">4星</MenuItem>
            <MenuItem value="5">5星</MenuItem>
          </Select>
        </Box>
        <Button
          variant="outlined"
          size="small"
          onClick={handleApply}
          className="fn-feedback-apply-btn"
        >
          套用
        </Button>
      </Box>

      {error ? (
        <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
      ) : (
        <Box className="fn-feedback-grid-wrap">
          {isLoading ? (
            <Box className="fn-feedback-loading">
              <CircularProgress />
            </Box>
          ) : (
            <DataGrid
              rows={feedbacks}
              columns={columns}
              getRowId={(row) => row.id}
              pageSizeOptions={[10, 25]}
              initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
              disableRowSelectionOnClick
              rowHeight={36}
              columnHeaderHeight={36}
              localeText={{ noRowsLabel: '尚無回饋資料' }}
              sx={{
                border: 'none',
                '& .MuiDataGrid-columnHeaders': { bgcolor: '#f1f5f9' },
                '& .MuiDataGrid-cell': { display: 'flex', alignItems: 'center' },
                '& .MuiDataGrid-footerContainer': { minHeight: 36, height: 36, overflow: 'hidden' },
                '& .MuiTablePagination-toolbar': { minHeight: 36, height: 36, padding: '0 8px' },
              }}
            />
          )}
        </Box>
      )}
    </Box>
  )
}
