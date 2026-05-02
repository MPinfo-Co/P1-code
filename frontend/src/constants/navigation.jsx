import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined'
import MenuBookOutlinedIcon from '@mui/icons-material/MenuBookOutlined'
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined'
import PeopleAltOutlinedIcon from '@mui/icons-material/PeopleAltOutlined'
import ManageAccountsIcon from '@mui/icons-material/ManageAccounts'
import TuneOutlinedIcon from '@mui/icons-material/TuneOutlined'

export const FOLDERS = [
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
      {
        fnKey: 'fn_setting',
        label: '系統參數',
        path: '/settings/setting',
        icon: <SettingsOutlinedIcon fontSize="small" />,
      },
    ],
  },
]
