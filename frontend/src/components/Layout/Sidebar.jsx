import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../stores/authStore'
import { ICON_MAP } from '../../constants/navigation'
import { useNavigationQuery } from '../../queries/useNavigationQuery'
import Drawer from '@mui/material/Drawer'
import List from '@mui/material/List'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Collapse from '@mui/material/Collapse'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

const DRAWER_WIDTH = 260

const iconSx = { color: '#94a3b8', minWidth: 36 }
const textSx = { '& .MuiListItemText-primary': { fontSize: 14, fontWeight: 500, color: '#94a3b8' } }
const activeSx = {
  borderLeft: '4px solid #6366f1',
  bgcolor: '#1e293b',
  '& .MuiListItemText-primary': { color: 'white', fontWeight: 600 },
  '& .MuiListItemIcon-root': { color: 'white' },
}

export default function Sidebar() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { data: navFolders = [] } = useNavigationQuery()

  const [openFolders, setOpenFolders] = useState({})

  const allowedFunctions = user && Array.isArray(user.functions) ? new Set(user.functions) : null

  function handleToggleFolder(code) {
    setOpenFolders((prev) => ({ ...prev, [code]: !prev[code] }))
  }

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          bgcolor: '#0f172a',
          borderRight: 'none',
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      {/* Brand */}
      <Box
        onClick={() => navigate('/fn_partner')}
        sx={{
          px: 3,
          height: 40,
          display: 'flex',
          alignItems: 'center',
          borderBottom: '1px solid #1e293b',
          cursor: 'pointer',
        }}
      >
        <Typography sx={{ fontSize: 22, fontWeight: 800, color: 'white' }}>MP-Box</Typography>
      </Box>

      {/* Nav */}
      <List sx={{ flex: 1, py: 1.5 }} disablePadding>
        {navFolders.map((folder) => {
          const visibleItems = allowedFunctions
            ? folder.items.filter((item) => allowedFunctions.has(item.function_code))
            : []
          if (visibleItems.length === 0) return null
          const isOpen = openFolders[folder.folder_code]
          return (
            <Box key={folder.folder_code}>
              <ListItemButton
                onClick={() => handleToggleFolder(folder.folder_code)}
                sx={{ px: 3, py: '2px', minHeight: 0, '&:hover': { bgcolor: '#1e293b' } }}
              >
                <ListItemIcon sx={iconSx}>{ICON_MAP[folder.folder_code]}</ListItemIcon>
                <ListItemText primary={folder.folder_label} sx={textSx} />
                {isOpen ? (
                  <ExpandLessIcon sx={{ color: '#94a3b8', fontSize: 18 }} />
                ) : (
                  <ExpandMoreIcon sx={{ color: '#94a3b8', fontSize: 18 }} />
                )}
              </ListItemButton>
              <Collapse in={isOpen} timeout="auto" unmountOnExit>
                <List disablePadding sx={{ bgcolor: '#0b1120' }}>
                  {visibleItems.map((item) => (
                    <NavLink
                      key={item.function_code}
                      to={`/${item.function_code.replace(/^fn_/, '')}`}
                      style={{ textDecoration: 'none' }}
                    >
                      {({ isActive }) => (
                        <ListItemButton
                          sx={{
                            pl: 7,
                            py: '2px',
                            minHeight: 0,
                            ...(isActive ? activeSx : { '&:hover': { bgcolor: '#1e293b' } }),
                          }}
                        >
                          <ListItemIcon sx={{ ...iconSx, minWidth: 28 }}>
                            {ICON_MAP[item.function_code]}
                          </ListItemIcon>
                          <ListItemText
                            primary={item.function_label}
                            sx={{
                              '& .MuiListItemText-primary': {
                                fontSize: 13,
                                color: isActive ? 'white' : '#94a3b8',
                              },
                            }}
                          />
                        </ListItemButton>
                      )}
                    </NavLink>
                  ))}
                </List>
              </Collapse>
            </Box>
          )
        })}
      </List>

      <Box sx={{ px: 3, py: 1.5, borderTop: '1px solid #1e293b' }}>
        <Typography sx={{ fontSize: 11, color: '#475569' }}>v73</Typography>
      </Box>
    </Drawer>
  )
}
