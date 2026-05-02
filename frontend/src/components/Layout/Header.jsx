import { useLocation } from 'react-router-dom'
import { useAuth } from '../../stores/authStore'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import { FOLDERS } from '../../constants/navigation'

const NAV_ITEMS = FOLDERS.flatMap((f) => f.items)

export default function Header() {
  const { logout } = useAuth()
  const { pathname } = useLocation()

  const title =
    NAV_ITEMS.filter((item) => pathname === item.path || pathname.startsWith(item.path + '/'))
      .sort((a, b) => b.path.length - a.path.length)[0]?.label ?? 'MP-Box'

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{ bgcolor: 'white', borderBottom: '1px solid #e2e8f0' }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', minHeight: '40px !important', px: '20px' }}>
        <Typography variant="h6" sx={{ fontWeight: 800, color: '#1e293b' }}>
          {title}
        </Typography>
        <Button
          onClick={logout}
          sx={{ color: '#ef4444', fontWeight: 600, '&:hover': { bgcolor: '#fef2f2' } }}
        >
          登出
        </Button>
      </Toolbar>
    </AppBar>
  )
}
