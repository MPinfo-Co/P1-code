import { Outlet } from 'react-router-dom'
import { Box } from '@mui/material'
import Sidebar from './Sidebar'
import Header from './Header'

export default function Layout() {
  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Sidebar />
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Header />
        <Box component="main" sx={{ flex: 1, overflow: 'auto', bgcolor: '#f8fafc', p: 4 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  )
}
