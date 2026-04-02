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
import ManageAccountsOutlinedIcon from '@mui/icons-material/ManageAccountsOutlined'
import GroupsOutlinedIcon from '@mui/icons-material/GroupsOutlined'
import TuneOutlinedIcon from '@mui/icons-material/TuneOutlined'
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
  const [settingOpen, setSettingOpen] = useState(false)
  const { user } = useAuth()
  const navigate = useNavigate()
  const canSeeSetting = user?.role === '管理員'

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
        sx={{ px: 3, py: 2.5, borderBottom: '1px solid #1e293b', cursor: 'pointer' }}
      >
        <Typography sx={{ fontSize: 22, fontWeight: 800, color: 'white' }}>MP-Box</Typography>
      </Box>

      {/* Nav */}
      <List sx={{ flex: 1, py: 1.5 }} disablePadding>
        <NavLink to="/ai-partner" style={{ textDecoration: 'none' }}>
          {({ isActive }) => (
            <ListItemButton
              sx={{
                px: 3,
                py: 1.2,
                ...(isActive ? activeSx : { '&:hover': { bgcolor: '#1e293b' } }),
              }}
            >
              <ListItemIcon sx={iconSx}>
                <SmartToyOutlinedIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="AI夥伴" sx={textSx} />
            </ListItemButton>
          )}
        </NavLink>

        <NavLink to="/kb" style={{ textDecoration: 'none' }}>
          {({ isActive }) => (
            <ListItemButton
              sx={{
                px: 3,
                py: 1.2,
                ...(isActive ? activeSx : { '&:hover': { bgcolor: '#1e293b' } }),
              }}
            >
              <ListItemIcon sx={iconSx}>
                <MenuBookOutlinedIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="知識庫" sx={textSx} />
            </ListItemButton>
          )}
        </NavLink>

        {canSeeSetting && (
          <>
            <ListItemButton
              onClick={() => setSettingOpen((o) => !o)}
              sx={{ px: 3, py: 1.2, '&:hover': { bgcolor: '#1e293b' } }}
            >
              <ListItemIcon sx={iconSx}>
                <SettingsOutlinedIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText primary="設定" sx={textSx} />
              {settingOpen ? (
                <ExpandLessIcon sx={{ color: '#94a3b8', fontSize: 18 }} />
              ) : (
                <ExpandMoreIcon sx={{ color: '#94a3b8', fontSize: 18 }} />
              )}
            </ListItemButton>
            <Collapse in={settingOpen} timeout="auto" unmountOnExit>
              <List disablePadding sx={{ bgcolor: '#0b1120' }}>
                {[
                  {
                    to: '/settings/account',
                    label: '帳號',
                    icon: <ManageAccountsOutlinedIcon fontSize="small" />,
                  },
                  {
                    to: '/settings/role',
                    label: '角色',
                    icon: <GroupsOutlinedIcon fontSize="small" />,
                  },
                  {
                    to: '/settings/ai-config',
                    label: 'AI夥伴管理',
                    icon: <TuneOutlinedIcon fontSize="small" />,
                  },
                ].map((item) => (
                  <NavLink key={item.to} to={item.to} style={{ textDecoration: 'none' }}>
                    {({ isActive }) => (
                      <ListItemButton
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
          </>
        )}
      </List>

      <Box sx={{ px: 3, py: 1.5, borderTop: '1px solid #1e293b' }}>
        <Typography sx={{ fontSize: 11, color: '#475569' }}>v73</Typography>
      </Box>
    </Drawer>
  )
}
