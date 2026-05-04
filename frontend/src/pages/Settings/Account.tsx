import { useState } from 'react'
import { users as initialUsers, type MockUser } from '@/data/users'
import { DataGrid, type GridColDef } from '@mui/x-data-grid'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Chip from '@mui/material/Chip'
import Checkbox from '@mui/material/Checkbox'
import FormControlLabel from '@mui/material/FormControlLabel'
import './Account.css'

const ROLE_OPTIONS = ['管理員', '一般使用者', '資安分析師']

interface AppliedFilter {
  role: string
  keyword: string
}

export default function Account() {
  const [userList, setUserList] = useState<MockUser[]>(initialUsers)
  const [modalOpen, setModalOpen] = useState(false)
  const [newName, setNewName] = useState('')
  const [newEmail, setNewEmail] = useState('')
  const [newRoles, setNewRoles] = useState<string[]>([])
  const [filterRole, setFilterRole] = useState('all')
  const [filterKeyword, setFilterKeyword] = useState('')
  const [applied, setApplied] = useState<AppliedFilter>({ role: 'all', keyword: '' })

  function handleSave() {
    setModalOpen(false)
    setNewName('')
    setNewEmail('')
    setNewRoles([])
  }

  function toggleRole(r: string) {
    setNewRoles((prev) => (prev.includes(r) ? prev.filter((x) => x !== r) : [...prev, r]))
  }

  const filtered = userList.filter((u) => {
    if (applied.role !== 'all' && !u.roles.includes(applied.role)) return false
    if (applied.keyword) {
      const kw = applied.keyword.toLowerCase()
      if (!u.name.toLowerCase().includes(kw) && !u.email.toLowerCase().includes(kw)) return false
    }
    return true
  })

  const columns: GridColDef<MockUser>[] = [
    {
      field: 'name',
      headerName: '姓名',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{value}</Typography>
      ),
    },
    {
      field: 'email',
      headerName: '電子信箱',
      flex: 1.5,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{value}</Typography>
      ),
    },
    {
      field: 'roles',
      headerName: '角色',
      flex: 1,
      renderCell: ({ value }) =>
        (value as string[]).map((r) => (
          <Chip
            key={r}
            label={r}
            size="small"
            sx={{ mr: 0.5, fontSize: 11, bgcolor: '#eef1f8', color: '#2e3f6e' }}
          />
        )),
    },
    {
      field: 'actions',
      headerName: '執行動作',
      width: 160,
      sortable: false,
      renderCell: ({ row }) => (
        <Box className="account-actions-cell">
          <Button size="small" variant="outlined" className="account-action-btn">
            編輯
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            className="account-action-btn-error"
            onClick={() => setUserList((u) => u.filter((x) => x.id !== row.id))}
          >
            刪除
          </Button>
        </Box>
      ),
    },
  ]

  return (
    <Box>
      <Box className="account-header">
        <Typography variant="h6" className="account-title">
          使用者管理
        </Typography>
        <Button
          variant="contained"
          onClick={() => {
            setNewName('')
            setNewEmail('')
            setNewRoles([])
            setModalOpen(true)
          }}
        >
          新增使用者
        </Button>
      </Box>

      <Box className="account-filter-bar">
        <FormControl size="small" className="account-role-select">
          <InputLabel>角色職位</InputLabel>
          <Select
            value={filterRole}
            label="角色職位"
            onChange={(e) => setFilterRole(e.target.value)}
          >
            <MenuItem value="all">全部</MenuItem>
            {ROLE_OPTIONS.map((r) => (
              <MenuItem key={r} value={r}>
                {r}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField
          size="small"
          label="關鍵字搜尋"
          placeholder="搜尋姓名或信箱..."
          value={filterKeyword}
          onChange={(e) => setFilterKeyword(e.target.value)}
          className="account-keyword-input"
        />
        <Button
          variant="outlined"
          onClick={() => setApplied({ role: filterRole, keyword: filterKeyword })}
          className="account-apply-btn"
        >
          套用
        </Button>
      </Box>

      <Box className="account-grid-wrap">
        <DataGrid
          rows={filtered}
          columns={columns}
          pageSizeOptions={[10, 25]}
          initialState={{ pagination: { paginationModel: { pageSize: 10 } } }}
          disableRowSelectionOnClick
          sx={{ border: 'none' }}
        />
      </Box>

      <Dialog open={modalOpen} onClose={() => setModalOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle className="account-dialog-title">新增使用者</DialogTitle>
        <DialogContent
          sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}
        >
          <TextField
            label="名稱"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            fullWidth
            size="small"
          />
          <TextField
            label="Email"
            type="email"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            fullWidth
            size="small"
          />
          <Box>
            <Box className="account-roles-header">
              <Typography className="account-roles-header-title">角色</Typography>
              <Button
                size="small"
                onClick={() =>
                  setNewRoles(newRoles.length === ROLE_OPTIONS.length ? [] : [...ROLE_OPTIONS])
                }
                className="account-toggle-all"
              >
                全選
              </Button>
            </Box>
            <Box className="account-roles-list">
              {ROLE_OPTIONS.map((r) => (
                <FormControlLabel
                  key={r}
                  control={
                    <Checkbox
                      size="small"
                      checked={newRoles.includes(r)}
                      onChange={() => toggleRole(r)}
                      sx={{ color: '#2e3f6e', '&.Mui-checked': { color: '#2e3f6e' } }}
                    />
                  }
                  label={<Typography sx={{ fontSize: 13 }}>{r}</Typography>}
                  sx={{
                    display: 'flex',
                    mb: 0.5,
                    bgcolor: 'white',
                    borderRadius: 1,
                    border: '1px solid #e2e8f0',
                    px: 1,
                    mx: 0,
                  }}
                />
              ))}
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setModalOpen(false)} className="account-cancel-btn">
            取消
          </Button>
          <Button onClick={handleSave} variant="contained">
            儲存
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
