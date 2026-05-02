import { useLocation } from 'react-router-dom'
import { useAuth } from '../../stores/authStore'
import { useNavigationQuery } from '../../queries/useNavigationQuery'
import AppBar from '@mui/material/AppBar'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'

export default function Header() {
  const { logout } = useAuth()
  const { pathname } = useLocation()
  const { data: navFolders = [] } = useNavigationQuery()

  const navItems = navFolders.flatMap((f) => f.items)
  const title =
    navItems
      .filter(
        (item) =>
          pathname === `/${item.function_code}` ||
          pathname.startsWith(`/${item.function_code}/`)
      )
      .sort((a, b) => b.function_code.length - a.function_code.length)[0]
      ?.function_label ?? 'MP-Box'

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
