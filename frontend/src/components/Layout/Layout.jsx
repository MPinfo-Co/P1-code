import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Box } from '@mui/material'
import Sidebar from './Sidebar'
import Header from './Header'

export default function Layout() {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)

  function handleOpenSidebar() {
    setIsMobileSidebarOpen(true)
  }

  function handleCloseSidebar() {
    setIsMobileSidebarOpen(false)
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Sidebar isMobileOpen={isMobileSidebarOpen} onClose={handleCloseSidebar} />
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Header onOpenSidebar={handleOpenSidebar} />
        <Box
          component="main"
          sx={{ flex: 1, overflow: 'auto', bgcolor: '#f0f4f8', p: '14px 20px' }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  )
}
