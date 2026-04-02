import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import SecurityOutlinedIcon from '@mui/icons-material/SecurityOutlined'

export default function Home() {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 12,
        color: '#94a3b8',
      }}
    >
      <SecurityOutlinedIcon sx={{ fontSize: 64, color: '#cbd5e1', mb: 2.5 }} />
      <Typography variant="h4" sx={{ fontWeight: 900, color: '#1e293b', mb: 1 }}>
        歡迎進入 MP-Box 管理中心
      </Typography>
      <Typography sx={{ color: '#64748b' }}>請使用左側目錄來操作功能。</Typography>
    </Box>
  )
}
