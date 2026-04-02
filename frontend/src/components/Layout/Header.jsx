import { useLocation } from 'react-router-dom'
import { useAuth } from '../../stores/authStore'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'

const PAGE_TITLES = {
  '/': '首頁',
  '/ai-partner': 'AI夥伴',
  '/kb': '知識庫',
  '/settings/account': '帳號',
  '/settings/role': '角色',
  '/settings/ai-config': 'AI夥伴管理',
}

export default function Header() {
  const { logout } = useAuth()
  const { pathname } = useLocation()

  const title =
    Object.entries(PAGE_TITLES)
      .filter(([path]) => pathname === path || pathname.startsWith(path + '/'))
      .sort((a, b) => b[0].length - a[0].length)[0]?.[1] ?? 'MP-Box'

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{ bgcolor: 'white', borderBottom: '1px solid #e2e8f0' }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', minHeight: '70px !important' }}>
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
