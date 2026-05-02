// src/pages/fn_setting/FnSettingList.tsx
import { useState } from 'react'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import { useAuth } from '@/stores/authStore'
import {
  useSettingsQuery,
  useParamTypeOptionsQuery,
} from '@/queries/useSettingsQuery'
import type { SettingRow } from '@/queries/useSettingsQuery'
import FnSettingEdit from './FnSettingEdit'

interface AppliedFilter {
  param_type?: string
}

export default function FnSettingList() {
  const [filterType, setFilterType] = useState<string>('all')
  const [appliedFilter, setAppliedFilter] = useState<AppliedFilter>({})

  const [isEditOpen, setIsEditOpen] = useState(false)
  const [editingRow, setEditingRow] = useState<SettingRow | null>(null)

  // TODO: 等 GET /api/users/me 實作後改用 can_manage_settings 欄位判斷
  const { user } = useAuth()
  const isAdmin = !!user

  const { data: settings = [], isLoading, error } = useSettingsQuery(appliedFilter)
  const { data: paramTypeOptions = [] } = useParamTypeOptionsQuery()

  function handleApply() {
    const filter: AppliedFilter = {}
    if (filterType !== 'all') filter.param_type = filterType
    setAppliedFilter(filter)
  }

  function handleEditClick(row: SettingRow) {
    setEditingRow(row)
    setIsEditOpen(true)
  }

  const baseColumns: GridColDef<SettingRow>[] = [
    {
      field: 'param_type',
      headerName: '參數類型',
      flex: 1,
      renderCell: ({ value }) => (
        <Chip
          label={value}
          size="small"
          sx={{ fontSize: 12, bgcolor: '#e2e8f0', color: '#475569', borderRadius: '4px' }}
        />
      ),
    },
    {
      field: 'param_code',
      headerName: '參數代碼',
      flex: 1.5,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{value}</Typography>
      ),
    },
    {
      field: 'param_value',
      headerName: '參數值',
      flex: 2,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13 }}>{value}</Typography>
      ),
    },
  ]

  const actionColumn: GridColDef<SettingRow> = {
    field: 'actions',
    headerName: '操作',
    width: 100,
    sortable: false,
    renderCell: ({ row }) => (
      <Button
        size="small"
        variant="outlined"
        sx={{ fontSize: 12, borderColor: '#cbd5e1', color: '#64748b' }}
        onClick={() => handleEditClick(row)}
      >
        編輯
      </Button>
    ),
  }

  const columns = isAdmin ? [...baseColumns, actionColumn] : baseColumns

  return (
    <Box>
      {/* Filter bar */}
      <Box
        sx={{
          bgcolor: '#f1f5f9',
          borderRadius: '4px',
          padding: '3px 12px',
          mb: '5px',
          display: 'flex',
          gap: 2,
          flexWrap: 'nowrap',
          alignItems: 'center',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography sx={{ fontSize: 13, color: '#1e293b', fontWeight: 700, whiteSpace: 'nowrap' }}>
            參數類型:
          </Typography>
          <Select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            size="small"
            displayEmpty
            sx={{ height: 24, fontSize: 13, '& .MuiSelect-select': { py: '2px' } }}
          >
            <MenuItem value="all">全部</MenuItem>
            {paramTypeOptions.map((t) => (
              <MenuItem key={t} value={t}>
                {t}
              </MenuItem>
            ))}
          </Select>
        </Box>
        <Button
          variant="outlined"
          size="small"
          onClick={handleApply}
          sx={{ borderColor: '#2e3f6e', color: '#2e3f6e', borderRadius: '3px', height: 24, fontSize: 12 }}
        >
          套用
        </Button>
      </Box>

      {/* Data table */}
      {error ? (
        <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
      ) : (
        <Box
          sx={{
            bgcolor: 'white',
            borderRadius: '4px',
            border: '1px solid #e2e8f0',
            overflow: 'hidden',
          }}
        >
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
              <CircularProgress />
            </Box>
          ) : (
            <DataGrid
              rows={settings}
              columns={columns}
              getRowId={(row) => row.param_code}
              pageSizeOptions={[10, 25]}
              initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
              disableRowSelectionOnClick
              rowHeight={36}
              columnHeaderHeight={36}
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

      {/* Edit dialog */}
      <FnSettingEdit
        key={editingRow?.param_code ?? 'edit'}
        open={isEditOpen}
        row={editingRow}
        onClose={() => setIsEditOpen(false)}
        onSuccess={() => setIsEditOpen(false)}
      />
    </Box>
  )
}
