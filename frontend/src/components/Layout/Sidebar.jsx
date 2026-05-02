import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../stores/authStore'
import Drawer from '@mui/material/Drawer'
import List from '@mui/material/List'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Collapse from '@mui/material/Collapse'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined'
import MenuBookOutlinedIcon from '@mui/icons-material/MenuBookOutlined'
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'
import PeopleAltOutlinedIcon from '@mui/icons-material/PeopleAltOutlined'
import ManageAccountsIcon from '@mui/icons-material/ManageAccounts'
import TuneOutlinedIcon from '@mui/icons-material/TuneOutlined'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

const DRAWER_WIDTH = 260

// ── 目錄與功能定義（對應 tb_function_folder + tb_functions seed data）──
const FOLDERS = [
  {
    key: 'ai_partner',
    label: 'AI 夥伴',
    defaultOpen: true,
    icon: <SmartToyOutlinedIcon fontSize="small" />,
    items: [
      {
        fnKey: 'fn_partner',
        label: 'AI 夥伴',
        path: '/ai-partner',
        icon: <SmartToyOutlinedIcon fontSize="small" />,
      },
      {
        fnKey: 'fn_km',
        label: '知識庫',
        path: '/kb',
        icon: <MenuBookOutlinedIcon fontSize="small" />,
      },
      {
        fnKey: 'fn_ai_config',
        label: 'AI 夥伴管理',
        path: '/settings/ai-config',
        icon: <TuneOutlinedIcon fontSize="small" />,
      },
    ],
  },
  {
    key: 'settings',
    label: '設定',
    defaultOpen: false,
    icon: <SettingsOutlinedIcon fontSize="small" />,
    items: [
      {
        fnKey: 'fn_user',
        label: '使用者管理',
        path: '/settings/account',
        icon: <PeopleAltOutlinedIcon fontSize="small" />,
      },
      {
        fnKey: 'fn_role',
        label: '角色管理',
        path: '/settings/roles',
        icon: <ManageAccountsIcon fontSize="small" />,
      },
    ],
  },
]

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

  // Initialise open state from defaultOpen per folder
  const [openFolders, setOpenFolders] = useState(() => {
    const initial = {}
    FOLDERS.forEach((f) => {
      initial[f.key] = f.defaultOpen
    })
    return initial
  })

  // Derive allowed functions from user.functions (from GET /api/users/me)
  const allowedFunctions = user && Array.isArray(user.functions) ? new Set(user.functions) : null // null = not loaded yet; show nothing until resolved

  function handleToggleFolder(key) {
    setOpenFolders((prev) => ({ ...prev, [key]: !prev[key] }))
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
        onClick={() => navigate('/ai-partner')}
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

      {/* Nav — two-level: folder → items */}
      <List sx={{ flex: 1, py: 1.5 }} disablePadding>
        {FOLDERS.map((folder) => {
          // Filter visible items by user permissions
          const visibleItems = allowedFunctions
            ? folder.items.filter((item) => allowedFunctions.has(item.fnKey))
            : []

          // Hide entire folder if no items are accessible
          if (visibleItems.length === 0) return null

          const isOpen = openFolders[folder.key]

          return (
            <Box key={folder.key}>
              {/* Folder header */}
              <ListItemButton
                onClick={() => handleToggleFolder(folder.key)}
                sx={{ px: 3, py: 1.2, '&:hover': { bgcolor: '#1e293b' } }}
              >
                <ListItemIcon sx={iconSx}>{folder.icon}</ListItemIcon>
                <ListItemText primary={folder.label} sx={textSx} />
                {isOpen ? (
                  <ExpandLessIcon sx={{ color: '#94a3b8', fontSize: 18 }} />
                ) : (
                  <ExpandMoreIcon sx={{ color: '#94a3b8', fontSize: 18 }} />
                )}
              </ListItemButton>

              {/* Folder items */}
              <Collapse in={isOpen} timeout="auto" unmountOnExit>
                <List disablePadding sx={{ bgcolor: '#0b1120' }}>
                  {visibleItems.map((item) => (
                    <NavLink key={item.path} to={item.path} style={{ textDecoration: 'none' }}>
                      {({ isActive }) => (
                        <ListItemButton
                          sx={{
                          sx={{
                            pl: 7,
                            py: 1,
                            ...(isActive ? activeSx : { '&:hover': { bgcolor: '#1e293b' } }),
                          }}
                        >
                          <ListItemIcon sx={{ ...iconSx, minWidth: 28 }}>{item.icon}</ListItemIcon>
                          <ListItemText
                            primary={item.label}
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
