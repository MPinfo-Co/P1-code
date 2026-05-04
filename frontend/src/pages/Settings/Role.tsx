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
import { DataGrid, type GridColDef } from '@mui/x-data-grid'
import { users } from '@/data/users'
import './Role.css'

interface RoleRow {
  id: number | null
  name: string
  partners: string[]
  memberIds: number[]
  canAccessAI: boolean
  canManageAccounts: boolean
  canManageRoles: boolean
  canEditAI: boolean
  canManageKB: boolean
}

type PermissionKey =
  | 'canAccessAI'
  | 'canManageAccounts'
  | 'canManageRoles'
  | 'canEditAI'
  | 'canManageKB'

const initialRoles: RoleRow[] = [
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

const PERMISSIONS: { key: PermissionKey; label: string; desc: string }[] = [
  { key: 'canAccessAI', label: 'AI 夥伴', desc: '可使用 AI 夥伴進行分析' },
  { key: 'canManageAccounts', label: '使用者管理', desc: '可新增、修改、刪除使用者' },
  { key: 'canManageRoles', label: '角色管理', desc: '可新增、修改、刪除角色與權限' },
  { key: 'canEditAI', label: 'AI 夥伴管理', desc: '可調整 AI 夥伴設定與綁定知識庫' },
  { key: 'canManageKB', label: '知識庫管理', desc: '可新增、編輯知識庫及上傳文件與資料表' },
]

function emptyRole(): RoleRow {
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
  const [roleList, setRoleList] = useState<RoleRow[]>(initialRoles)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<RoleRow>(emptyRole())
  const [keyword, setKeyword] = useState('')
  const [applied, setApplied] = useState('')

  function openAdd() {
    setEditing(emptyRole())
    setModalOpen(true)
  }
  function openEdit(role: RoleRow) {
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

  function deleteRole(id: number | null) {
    if (id == null) return
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

  const columns: GridColDef<RoleRow>[] = [
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
        (value as string[])?.includes('資安專家') ? (
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
        <Box className="role-actions-cell">
          <Button
            size="small"
            variant="outlined"
            className="role-action-btn"
            onClick={() => openEdit(row)}
          >
            編輯
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            className="role-action-btn-error"
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
      <Box className="role-header">
        <Typography className="role-title">角色設定</Typography>
        <Button variant="contained" onClick={openAdd} className="role-add-btn">
          新增角色
        </Button>
      </Box>

      <Box className="role-filter-bar">
        <Typography className="role-filter-label">關鍵字搜尋:</Typography>
        <TextField
          size="small"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="搜尋角色名稱..."
          className="role-filter-input"
          sx={{ '& .MuiInputBase-input': { fontSize: 13 } }}
        />
        <Button variant="outlined" onClick={() => setApplied(keyword)} className="role-apply-btn">
          套用
        </Button>
      </Box>

      <Box className="role-grid-wrap">
        <DataGrid
          rows={filtered}
          columns={columns}
          autoHeight
          disableRowSelectionOnClick
          hideFooter={filtered.length <= 100}
          getRowId={(row) => row.id ?? -1}
          sx={{
            border: 'none',
            '& .MuiDataGrid-columnHeaders': { bgcolor: '#f1f5f9' },
            '& .MuiDataGrid-columnHeaderTitle': { fontWeight: 800, fontSize: 14, color: '#1e293b' },
            '& .MuiDataGrid-cell': { display: 'flex', alignItems: 'center' },
            '& .MuiDataGrid-row': { borderBottom: '1px solid #f1f5f9' },
          }}
        />
      </Box>

      <Dialog open={modalOpen} onClose={() => setModalOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle className="role-dialog-title">
          {editing.id ? '編輯角色' : '新增角色'}
        </DialogTitle>
        <DialogContent sx={{ pt: '16px !important' }}>
          <Box className="role-form-stack">
            <Box>
              <Typography className="role-form-label">角色名稱</Typography>
              <TextField
                fullWidth
                size="small"
                value={editing.name}
                onChange={(e) => setEditing((v) => ({ ...v, name: e.target.value }))}
                placeholder="輸入角色名稱"
                sx={{ '& .MuiInputBase-input': { fontSize: 14 } }}
              />
            </Box>

            <Box>
              <Box className="role-section-header">
                <Typography className="role-form-label" sx={{ mb: 0 }}>
                  成員
                </Typography>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={toggleAllMembers}
                  className="role-toggle-all-btn"
                >
                  全選
                </Button>
              </Box>
              <Box className="role-members-box">
                {users.map((u) => (
                  <Box key={u.id} component="label" className="role-member-row">
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
                      className="role-member-checkbox"
                    />
                    <Typography className="role-member-name">{u.name}</Typography>
                    <Typography className="role-member-email">{u.email}</Typography>
                  </Box>
                ))}
              </Box>
            </Box>

            <Box>
              <Box className="role-section-header">
                <Typography className="role-form-label" sx={{ mb: 0 }}>
                  可用 AI 夥伴
                </Typography>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={toggleAllPartners}
                  className="role-toggle-all-btn"
                >
                  全選
                </Button>
              </Box>
              <Box className="role-partners-box">
                {ALL_PARTNERS.map((p) => (
                  <Box
                    key={p.id}
                    component="label"
                    className={`role-partner-row ${p.disabled ? 'role-partner-row-disabled' : ''}`}
                    sx={{ cursor: p.disabled ? 'default' : 'pointer' }}
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
                      className="role-member-checkbox"
                    />
                    <Typography className="role-partner-name">{p.name}</Typography>
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
                      <Typography className="role-partner-disabled-text">停用中</Typography>
                    )}
                  </Box>
                ))}
              </Box>
            </Box>

            <Box className="role-permissions-box">
              <Typography className="role-permissions-title">🔐 功能權限</Typography>
              {PERMISSIONS.map((perm, i) => (
                <Box
                  key={perm.key}
                  component="label"
                  className={`role-permission-row ${
                    i < PERMISSIONS.length - 1 ? 'role-permission-row-mb' : ''
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={!!editing[perm.key]}
                    onChange={() => setEditing((v) => ({ ...v, [perm.key]: !v[perm.key] }))}
                    className="role-permission-checkbox"
                  />
                  <Box>
                    <Typography component="strong" className="role-permission-label">
                      {perm.label}
                    </Typography>
                    <Typography className="role-permission-desc">{perm.desc}</Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setModalOpen(false)} className="role-cancel-btn">
            取消
          </Button>
          <Button onClick={saveRole} variant="contained" className="role-save-btn">
            儲存
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
