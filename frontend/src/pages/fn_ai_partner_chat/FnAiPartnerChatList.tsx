// src/pages/fn_ai_partner_chat/FnAiPartnerChatList.tsx
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import { DataGrid } from '@mui/x-data-grid'
import type { GridColDef } from '@mui/x-data-grid'
import { useAiPartnersQuery } from '@/queries/useAiPartnerChatQuery'
import type { AiPartner } from '@/queries/useAiPartnerChatQuery'

interface Props {
  onEnterChat: (partner: AiPartner) => void
}

export default function FnAiPartnerChatList({ onEnterChat }: Props) {
  const { data: partners = [], isLoading, error } = useAiPartnersQuery()

  const columns: GridColDef[] = [
    {
      field: 'name',
      headerName: 'AI 夥伴',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{value}</Typography>
      ),
    },
    {
      field: 'description',
      headerName: '功能說明',
      flex: 2,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{value}</Typography>
      ),
    },
    {
      field: 'actions',
      headerName: '操作',
      width: 120,
      sortable: false,
      renderCell: ({ row }: { row: AiPartner }) => (
        <Button
          size="small"
          variant="outlined"
          onClick={() => onEnterChat(row)}
          sx={{
            fontSize: 12,
            height: 26,
            borderRadius: '3px',
            borderColor: '#6366f1',
            color: '#6366f1',
            '&:hover': { bgcolor: '#f0f0ff', borderColor: '#4f46e5' },
          }}
        >
          進入對話
        </Button>
      ),
    },
  ]

  if (error) {
    return <Alert severity="error">載入失敗：{(error as Error).message}</Alert>
  }

  return (
    <Box>
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </Box>
      ) : partners.length === 0 ? (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            py: 6,
            bgcolor: '#f8fafc',
            borderRadius: 2,
            border: '1px solid #e2e8f0',
          }}
        >
          <Typography sx={{ fontSize: 14, color: '#64748b' }}>
            目前尚無可用的 AI 夥伴，請聯繫管理員
          </Typography>
        </Box>
      ) : (
        <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 1, overflow: 'hidden' }}>
          <DataGrid
            rows={partners}
            columns={columns}
            getRowId={(row) => row.id}
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
        </Box>
      )}
    </Box>
  )
}
