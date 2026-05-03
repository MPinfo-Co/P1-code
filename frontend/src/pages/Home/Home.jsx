import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

export default function Home() {
  return (
    <Box sx={{ p: '14px 20px' }}>
      <Typography sx={{ fontSize: 13, color: '#94a3b8', textAlign: 'center', mt: 2 }}>
        請使用左側目錄來操作功能。
      </Typography>
    </Box>
  )
}
