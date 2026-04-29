// src/pages/fn_notice/FnNoticeBlock.tsx
import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import CircularProgress from '@mui/material/CircularProgress'
import Alert from '@mui/material/Alert'
import CampaignOutlinedIcon from '@mui/icons-material/CampaignOutlined'
import { useNoticesQuery } from '@/queries/useNoticesQuery'
import FnNoticeForm from './FnNoticeForm'

export default function FnNoticeBlock() {
  const [isFormOpen, setIsFormOpen] = useState(false)
  const { data, isLoading, error } = useNoticesQuery()

  const notices = data?.data ?? []
  const canManage = data?.can_manage ?? false

  return (
    <Box
      sx={{
        bgcolor: 'white',
        border: '1px solid #e2e8f0',
        borderRadius: '4px',
        overflow: 'hidden',
        mb: 3,
      }}
    >
      {/* Header */}
      <Box
        sx={{
          bgcolor: '#f1f5f9',
          px: 2,
          py: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          borderBottom: '1px solid #e2e8f0',
        }}
      >
        <CampaignOutlinedIcon sx={{ fontSize: 18, color: '#475569' }} />
        <Typography sx={{ fontSize: 14, fontWeight: 700, color: '#1e293b', flex: 1 }}>
          系統公告
        </Typography>
        {canManage && (
          <Button
            variant="contained"
            size="small"
            onClick={() => setIsFormOpen(true)}
            sx={{ height: 24, fontSize: 12, borderRadius: '3px' }}
          >
            新增公告
          </Button>
        )}
      </Box>

      {/* Content */}
      <Box sx={{ px: 2, py: 1.5 }}>
        {error ? (
          <Alert severity="error" sx={{ fontSize: 13 }}>
            載入失敗：{(error as Error).message}
          </Alert>
        ) : isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
            <CircularProgress size={24} />
          </Box>
        ) : notices.length === 0 ? (
          <Typography sx={{ fontSize: 13, color: '#94a3b8', py: 1 }}>目前無公告</Typography>
        ) : (
          <Box component="ul" sx={{ m: 0, p: 0, listStyle: 'none' }}>
            {notices.map((notice) => (
              <Box
                key={notice.id}
                component="li"
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  py: '6px',
                  borderBottom: '1px solid #f1f5f9',
                  '&:last-child': { borderBottom: 'none' },
                }}
              >
                <Typography sx={{ fontSize: 13, color: '#1e293b' }}>{notice.title}</Typography>
                <Typography sx={{ fontSize: 12, color: '#94a3b8', ml: 2, whiteSpace: 'nowrap' }}>
                  有效期限：{notice.expires_at}
                </Typography>
              </Box>
            ))}
          </Box>
        )}
      </Box>

      {/* New notice dialog */}
      <FnNoticeForm
        open={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSuccess={() => setIsFormOpen(false)}
      />
    </Box>
  )
}
