// src/components/Layout/PermissionGuard.tsx
// Wraps a page and shows a "no permission" message if the user lacks access.
import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import useAuthStore from '../../stores/authStore'

interface Props {
  fnKey: string
  children: ReactNode
}

export default function PermissionGuard({ fnKey, children }: Props) {
  const user = useAuthStore((s) => s.user)

  // While user profile is not yet loaded, render children optimistically
  // (ProtectedRoute already ensures token exists)
  if (!user || !Array.isArray(user.functions)) {
    return <>{children}</>
  }

  const hasPermission = user.functions.includes(fnKey)

  if (!hasPermission) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100%',
          gap: 2,
        }}
      >
        <Typography variant="h6" sx={{ color: '#1e293b', fontWeight: 600 }}>
          您沒有存取此功能的權限
        </Typography>
        <Link to="/" style={{ fontSize: 14, color: '#6366f1' }}>
          返回首頁
        </Link>
      </Box>
    )
  }

  return <>{children}</>
}
