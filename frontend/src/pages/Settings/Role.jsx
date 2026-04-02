import { useState } from 'react'
import {
  Box,
  Typography,
  Button,
  Chip,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import { users } from '../../data/users'

const initialRoles = [
  {
    id: 1,
    name: '管理員',
    partners: ['資安專家'],
    memberIds: [1, 4, 5],
    canAccessAI: true,
    canManageAccounts: true,
    canManageRoles: true,
    canEditAI: true,
    canManageKB: true,
  },
  {
    id: 2,
    name: '一般使用者',
    partners: ['資安專家'],
    memberIds: [2, 3],
    canAccessAI: true,
    canManageAccounts: false,
    canManageRoles: false,
    canEditAI: false,
    canManageKB: false,
  },
]

const ALL_PARTNERS = [
  { id: 'security-expert', name: '資安專家', builtin: true, disabled: false },
  { id: 'order-secretary', name: '訂單智能秘書', builtin: false, disabled: true },
]

const PERMISSIONS = [
  { key: 'canAccessAI', label: 'AI 夥伴', desc: '可使用 AI 夥伴進行分析' },
  { key: 'canManageAccounts', label: '帳號管理', desc: '可新增、修改、刪除使用者帳號' },
  { key: 'canManageRoles', label: '角色管理', desc: '可新增、修改、刪除角色與權限' },
  { key: 'canEditAI', label: 'AI 夥伴管理', desc: '可調整 AI 夥伴設定與綁定知識庫' },
  { key: 'canManageKB', label: '知識庫管理', desc: '可新增、編輯知識庫及上傳文件與資料表' },
]

function emptyRole() {
  return {
    id: null,
    name: '',
    partners: [],
    memberIds: [],
    canAccessAI: false,
    canManageAccounts: false,
    canManageRoles: false,
    canEditAI: false,
    canManageKB: false,
  }
}

export default function Role() {
  const [roleList, setRoleList] = useState(initialRoles)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(emptyRole())
  const [keyword, setKeyword] = useState('')
  const [applied, setApplied] = useState('')

  function openAdd() {
    setEditing(emptyRole())
    setModalOpen(true)
  }
  function openEdit(role) {
    setEditing({ ...role })
    setModalOpen(true)
  }

  function saveRole() {
    if (!editing.name.trim()) {
      alert('請輸入角色名稱')
      return
    }
    if (editing.id) {
      setRoleList((prev) => prev.map((r) => (r.id === editing.id ? { ...editing } : r)))
    } else {
      setRoleList((prev) => [...prev, { ...editing, id: Date.now() }])
    }
    setModalOpen(false)
  }

  function deleteRole(id) {
    if (!window.confirm('確定要刪除此角色？')) return
    setRoleList((prev) => prev.filter((r) => r.id !== id))
  }

  function toggleAllMembers() {
    const allIds = users.map((u) => u.id)
    const allSelected = allIds.every((id) => (editing.memberIds || []).includes(id))
    setEditing((v) => ({ ...v, memberIds: allSelected ? [] : allIds }))
  }

  function toggleAllPartners() {
    const activeNames = ALL_PARTNERS.filter((p) => !p.disabled).map((p) => p.name)
    const allSelected = activeNames.every((n) => (editing.partners || []).includes(n))
    setEditing((v) => ({ ...v, partners: allSelected ? [] : activeNames }))
  }

  const filtered = roleList.filter(
    (r) => !applied || r.name.toLowerCase().includes(applied.toLowerCase())
  )

  const columns = [
    {
      field: 'name',
      headerName: '角色名稱',
      flex: 1,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{value}</Typography>
      ),
    },
    {
      field: 'partners',
      headerName: '資安專家存取權',
      flex: 1,
      renderCell: ({ value }) =>
        value?.includes('資安專家') ? (
          <Chip
            label="✓ 資安專家"
            size="small"
            sx={{ fontSize: 11, bgcolor: '#eef1f8', color: '#2e3f6e', fontWeight: 700 }}
          />
        ) : (
          <Typography sx={{ color: '#94a3b8' }}>—</Typography>
        ),
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
            onClick={() => openEdit(row)}
          >
            編輯
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            sx={{ fontSize: 12 }}
            onClick={() => deleteRole(row.id)}
          >
            刪除
          </Button>
        </Box>
      ),
    },
  ]

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography sx={{ fontSize: 20, fontWeight: 800, color: '#1e293b' }}>角色設定</Typography>
        <Button
          variant="contained"
          onClick={openAdd}
          sx={{
            bgcolor: '#2e3f6e',
            fontWeight: 700,
            fontSize: 14,
            '&:hover': { bgcolor: '#1e2d52' },
          }}
        >
          新增角色
        </Button>
      </Box>

      {/* Filter bar */}
      <Box
        sx={{
          bgcolor: 'white',
          borderRadius: 2,
          border: '1px solid #e2e8f0',
          p: 1.5,
          mb: 2,
          display: 'flex',
          gap: 1.5,
          alignItems: 'center',
        }}
      >
        <Typography sx={{ fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap' }}>
          關鍵字搜尋:
        </Typography>
        <TextField
          size="small"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="搜尋角色名稱..."
          sx={{ flex: 1, '& .MuiInputBase-input': { fontSize: 13 } }}
        />
        <Button
          variant="outlined"
          onClick={() => setApplied(keyword)}
          sx={{
            fontWeight: 600,
            fontSize: 13,
            borderColor: '#2e3f6e',
            color: '#2e3f6e',
            whiteSpace: 'nowrap',
            '&:hover': { bgcolor: '#eef1f8' },
          }}
        >
          套用
        </Button>
      </Box>

      {/* DataGrid */}
      <Box
        sx={{ bgcolor: 'white', borderRadius: 2, border: '1px solid #e2e8f0', overflow: 'hidden' }}
      >
        <DataGrid
          rows={filtered}
          columns={columns}
          autoHeight
          disableRowSelectionOnClick
          hideFooter={filtered.length <= 100}
          sx={{
            border: 'none',
            '& .MuiDataGrid-columnHeaders': { bgcolor: '#f1f5f9' },
            '& .MuiDataGrid-columnHeaderTitle': { fontWeight: 800, fontSize: 14, color: '#1e293b' },
            '& .MuiDataGrid-cell': { display: 'flex', alignItems: 'center' },
            '& .MuiDataGrid-row': { borderBottom: '1px solid #f1f5f9' },
          }}
        />
      </Box>

      {/* Role Dialog */}
      <Dialog open={modalOpen} onClose={() => setModalOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 800 }}>{editing.id ? '編輯角色' : '新增角色'}</DialogTitle>
        <DialogContent sx={{ pt: '16px !important' }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
            {/* 角色名稱 */}
            <Box>
              <Typography sx={{ fontWeight: 600, fontSize: 14, color: '#1e293b', mb: 0.75 }}>
                角色名稱
              </Typography>
              <TextField
                fullWidth
                size="small"
                value={editing.name}
                onChange={(e) => setEditing((v) => ({ ...v, name: e.target.value }))}
                placeholder="輸入角色名稱"
                sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
              />
            </Box>

            {/* 成員帳號 */}
            <Box>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  mb: 1,
                }}
              >
                <Typography sx={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>
                  成員帳號
                </Typography>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={toggleAllMembers}
                  sx={{
                    fontSize: 12,
                    borderColor: '#cbd5e1',
                    color: '#475569',
                    fontWeight: 600,
                    '&:hover': { bgcolor: '#f1f5f9' },
                  }}
                >
                  全選
                </Button>
              </Box>
              <Box
                sx={{
                  border: '1px solid #e2e8f0',
                  borderRadius: 2,
                  p: 0.5,
                  bgcolor: '#f8fafc',
                  maxHeight: 110,
                  overflowY: 'auto',
                }}
              >
                {users.map((u) => (
                  <Box
                    key={u.id}
                    component="label"
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.25,
                      p: '7px 10px',
                      borderRadius: 1.5,
                      cursor: 'pointer',
                      bgcolor: 'white',
                      mb: 0.5,
                      border: '1px solid #e2e8f0',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={(editing.memberIds || []).includes(u.id)}
                      onChange={() =>
                        setEditing((v) => ({
                          ...v,
                          memberIds: (v.memberIds || []).includes(u.id)
                            ? (v.memberIds || []).filter((x) => x !== u.id)
                            : [...(v.memberIds || []), u.id],
                        }))
                      }
                      style={{ width: 15, height: 15, accentColor: '#2e3f6e' }}
                    />
                    <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                      {u.name}
                    </Typography>
                    <Typography sx={{ fontSize: 12, color: '#94a3b8', flex: 1 }}>
                      {u.email}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>

            {/* 可用 AI 夥伴 */}
            <Box>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  mb: 1,
                }}
              >
                <Typography sx={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>
                  可用 AI 夥伴
                </Typography>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={toggleAllPartners}
                  sx={{
                    fontSize: 12,
                    borderColor: '#cbd5e1',
                    color: '#475569',
                    fontWeight: 600,
                    '&:hover': { bgcolor: '#f1f5f9' },
                  }}
                >
                  全選
                </Button>
              </Box>
              <Box
                sx={{ border: '1px solid #e2e8f0', borderRadius: 2, p: 0.5, bgcolor: '#f8fafc' }}
              >
                {ALL_PARTNERS.map((p) => (
                  <Box
                    key={p.id}
                    component="label"
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.25,
                      p: '8px 10px',
                      borderRadius: 1.5,
                      cursor: p.disabled ? 'default' : 'pointer',
                      bgcolor: 'white',
                      mb: 0.5,
                      border: '1px solid #e2e8f0',
                      opacity: p.disabled ? 0.5 : 1,
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={(editing.partners || []).includes(p.name)}
                      disabled={p.disabled}
                      onChange={() =>
                        !p.disabled &&
                        setEditing((v) => ({
                          ...v,
                          partners: (v.partners || []).includes(p.name)
                            ? (v.partners || []).filter((x) => x !== p.name)
                            : [...(v.partners || []), p.name],
                        }))
                      }
                      style={{ width: 15, height: 15, accentColor: '#2e3f6e' }}
                    />
                    <Typography sx={{ fontSize: 13 }}>{p.name}</Typography>
                    <Chip
                      label={p.builtin ? '預設' : '自訂'}
                      size="small"
                      sx={{
                        fontSize: 11,
                        fontWeight: 700,
                        bgcolor: p.builtin ? '#dbeafe' : '#f1f5f9',
                        color: p.builtin ? '#1d4ed8' : '#64748b',
                        height: 20,
                      }}
                    />
                    {p.disabled && (
                      <Typography sx={{ fontSize: 11, color: '#ef4444', fontWeight: 600 }}>
                        停用中
                      </Typography>
                    )}
                  </Box>
                ))}
              </Box>
            </Box>

            {/* 功能權限 */}
            <Box sx={{ p: 1.75, bgcolor: '#f8fafc', borderRadius: 2, border: '1px solid #e2e8f0' }}>
              <Typography sx={{ fontWeight: 700, mb: 1.5, color: '#1e293b', fontSize: 14 }}>
                🔐 功能權限
              </Typography>
              {PERMISSIONS.map((perm, i) => (
                <Box
                  key={perm.key}
                  component="label"
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.25,
                    p: 1,
                    borderRadius: 1.5,
                    bgcolor: 'white',
                    border: '1px solid #e2e8f0',
                    mb: i < PERMISSIONS.length - 1 ? 1 : 0,
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={!!editing[perm.key]}
                    onChange={() => setEditing((v) => ({ ...v, [perm.key]: !v[perm.key] }))}
                    style={{ width: 16, height: 16, accentColor: '#2e3f6e', cursor: 'pointer' }}
                  />
                  <Box>
                    <Typography
                      component="strong"
                      sx={{ display: 'block', fontSize: 13, fontWeight: 700 }}
                    >
                      {perm.label}
                    </Typography>
                    <Typography sx={{ fontSize: 12, color: '#64748b' }}>{perm.desc}</Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setModalOpen(false)} sx={{ color: '#64748b' }}>
            取消
          </Button>
          <Button
            onClick={saveRole}
            variant="contained"
            sx={{ bgcolor: '#2e3f6e', '&:hover': { bgcolor: '#1e2d52' } }}
          >
            儲存
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
