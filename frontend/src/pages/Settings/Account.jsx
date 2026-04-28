import { useState } from 'react'
import { users as initialUsers } from '../../data/users'
import { DataGrid } from '@mui/x-data-grid'
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

const ROLE_OPTIONS = ['管理員', '一般使用者', '資安分析師']

export default function Account() {
  const [userList, setUserList] = useState(initialUsers)
  const [modalOpen, setModalOpen] = useState(false)
  const [newName, setNewName] = useState('')
  const [newEmail, setNewEmail] = useState('')
  const [newRoles, setNewRoles] = useState([])
  const [filterRole, setFilterRole] = useState('all')
  const [filterKeyword, setFilterKeyword] = useState('')
  const [applied, setApplied] = useState({ role: 'all', keyword: '' })

  function handleSave() {
    setModalOpen(false)
    setNewName('')
    setNewEmail('')
    setNewRoles([])
  }

  function toggleRole(r) {
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

  const columns = [
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
        value.map((r) => (
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
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant="outlined"
            sx={{ fontSize: 12, borderColor: '#cbd5e1', color: '#64748b' }}
          >
            編輯
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            sx={{ fontSize: 12 }}
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 800, color: '#1e293b' }}>
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

      <Box
        sx={{
          bgcolor: 'white',
          borderRadius: 2,
          border: '1px solid #e2e8f0',
          p: 2,
          mb: 2,
          display: 'flex',
          gap: 2,
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <FormControl size="small" sx={{ minWidth: 140 }}>
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
          sx={{ width: 220 }}
        />
        <Button
          variant="outlined"
          onClick={() => setApplied({ role: filterRole, keyword: filterKeyword })}
          sx={{ borderColor: '#2e3f6e', color: '#2e3f6e' }}
        >
          套用
        </Button>
      </Box>

      <Box
        sx={{ bgcolor: 'white', borderRadius: 2, border: '1px solid #e2e8f0', overflow: 'hidden' }}
      >
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
        <DialogTitle sx={{ fontWeight: 800 }}>新增使用者</DialogTitle>
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
            <Box
              sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}
            >
              <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>角色</Typography>
              <Button
                size="small"
                onClick={() =>
                  setNewRoles(newRoles.length === ROLE_OPTIONS.length ? [] : [...ROLE_OPTIONS])
                }
                sx={{ fontSize: 12 }}
              >
                全選
              </Button>
            </Box>
            <Box sx={{ border: '1px solid #e2e8f0', borderRadius: 1, p: 1, bgcolor: '#f8fafc' }}>
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
          <Button onClick={() => setModalOpen(false)} sx={{ color: '#64748b' }}>
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
