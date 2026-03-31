import { useState } from 'react'
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

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-extrabold text-slate-800">角色設定</h2>
        <button
          onClick={openAdd}
          className="px-4 py-2 bg-[#2e3f6e] text-white rounded-lg text-sm font-bold hover:bg-[#1e2d52] transition-colors"
        >
          新增角色
        </button>
      </div>

      {/* Filter bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-3 mb-4 flex gap-3 items-center">
        <label className="text-sm font-semibold whitespace-nowrap">關鍵字搜尋:</label>
        <input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="搜尋角色名稱..."
          style={{
            height: 36,
            padding: '0 10px',
            border: '1px solid #cbd5e1',
            borderRadius: 6,
            fontSize: 13,
            outline: 'none',
            flex: 1,
          }}
        />
        <button
          onClick={() => setApplied(keyword)}
          style={{
            padding: '7px 16px',
            borderRadius: 6,
            cursor: 'pointer',
            fontWeight: 600,
            border: '1.5px solid #2e3f6e',
            background: 'white',
            color: '#2e3f6e',
            fontSize: 13,
            whiteSpace: 'nowrap',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = '#eef1f8')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
        >
          套用
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              {['角色名稱', '資安專家存取權', '執行動作'].map((h) => (
                <th
                  key={h}
                  className="text-left px-4 py-3.5 bg-slate-100 text-slate-800 font-extrabold text-sm border-b-2 border-slate-300"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((role) => (
              <tr key={role.id} className="border-b border-slate-100">
                <td className="px-4 py-3.5 text-sm font-semibold text-slate-700">{role.name}</td>
                <td className="px-4 py-3.5 text-sm">
                  {role.partners?.includes('資安專家') ? (
                    <span
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        padding: '2px 9px',
                        background: '#eef1f8',
                        color: '#2e3f6e',
                        borderRadius: 4,
                        fontSize: 12,
                        fontWeight: 700,
                        border: '1px solid #c5ccdf',
                      }}
                    >
                      ✓ 資安專家
                    </span>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
                <td className="px-4 py-3.5">
                  <div className="flex gap-2">
                    <button
                      onClick={() => openEdit(role)}
                      className="text-sm font-semibold text-slate-500 border border-slate-300 px-3 py-1 rounded-md hover:bg-slate-50"
                    >
                      編輯
                    </button>
                    <button
                      onClick={() => deleteRole(role.id)}
                      className="text-sm font-semibold text-red-500 border border-red-200 px-3 py-1 rounded-md hover:bg-red-50"
                    >
                      刪除
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Role Modal */}
      {modalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15,23,42,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: 'white',
              borderRadius: 12,
              padding: '24px 24px 0 24px',
              width: 480,
              maxHeight: '85vh',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
            }}
          >
            <h3
              style={{
                color: '#1e293b',
                marginBottom: 20,
                fontSize: 16,
                fontWeight: 800,
                flexShrink: 0,
              }}
            >
              {editing.id ? '編輯角色' : '新增角色'}
            </h3>

            <div
              style={{
                overflowY: 'auto',
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                gap: 18,
                paddingBottom: 4,
              }}
            >
              {/* 角色名稱 */}
              <div>
                <label
                  style={{
                    fontWeight: 600,
                    fontSize: 14,
                    color: '#1e293b',
                    display: 'block',
                    marginBottom: 6,
                  }}
                >
                  角色名稱
                </label>
                <input
                  value={editing.name}
                  onChange={(e) => setEditing((v) => ({ ...v, name: e.target.value }))}
                  placeholder="輸入角色名稱"
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    marginTop: 6,
                    height: 38,
                    padding: '0 10px',
                    border: '1.5px solid #e2e8f0',
                    borderRadius: 8,
                    fontSize: 14,
                    outline: 'none',
                  }}
                />
              </div>

              {/* 成員帳號 */}
              <div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 8,
                  }}
                >
                  <label style={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>
                    成員帳號
                  </label>
                  <button
                    onClick={toggleAllMembers}
                    style={{
                      padding: '3px 10px',
                      fontSize: 12,
                      border: '1px solid #cbd5e1',
                      borderRadius: 6,
                      background: 'white',
                      cursor: 'pointer',
                      fontWeight: 600,
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = '#f1f5f9')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
                  >
                    全選
                  </button>
                </div>
                <div
                  style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: 8,
                    padding: 4,
                    background: '#f8fafc',
                    maxHeight: 110,
                    overflowY: 'auto',
                  }}
                >
                  {users.map((u) => (
                    <label
                      key={u.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: '7px 10px',
                        borderRadius: 6,
                        cursor: 'pointer',
                        background: 'white',
                        marginBottom: 4,
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
                      <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                        {u.name}
                      </span>
                      <span style={{ fontSize: 12, color: '#94a3b8', flex: 1 }}>{u.email}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* 可用 AI 夥伴 */}
              <div>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 8,
                  }}
                >
                  <label style={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>
                    可用 AI 夥伴
                  </label>
                  <button
                    onClick={toggleAllPartners}
                    style={{
                      padding: '3px 10px',
                      fontSize: 12,
                      border: '1px solid #cbd5e1',
                      borderRadius: 6,
                      background: 'white',
                      cursor: 'pointer',
                      fontWeight: 600,
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = '#f1f5f9')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
                  >
                    全選
                  </button>
                </div>
                <div
                  style={{
                    border: '1px solid #e2e8f0',
                    borderRadius: 8,
                    padding: 4,
                    background: '#f8fafc',
                  }}
                >
                  {ALL_PARTNERS.map((p) => (
                    <label
                      key={p.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: '8px 10px',
                        borderRadius: 6,
                        cursor: p.disabled ? 'default' : 'pointer',
                        background: 'white',
                        marginBottom: 4,
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
                      <span style={{ fontSize: 13 }}>{p.name}</span>
                      <span
                        style={{
                          fontSize: 11,
                          padding: '1px 6px',
                          borderRadius: 4,
                          fontWeight: 700,
                          background: p.builtin ? '#dbeafe' : '#f1f5f9',
                          color: p.builtin ? '#1d4ed8' : '#64748b',
                        }}
                      >
                        {p.builtin ? '預設' : '自訂'}
                      </span>
                      {p.disabled && (
                        <span style={{ fontSize: 11, color: '#ef4444', fontWeight: 600 }}>
                          停用中
                        </span>
                      )}
                    </label>
                  ))}
                </div>
              </div>

              {/* 功能權限 */}
              <div
                style={{
                  padding: 14,
                  background: '#f8fafc',
                  borderRadius: 8,
                  border: '1px solid #e2e8f0',
                  marginBottom: 4,
                }}
              >
                <label
                  style={{
                    fontWeight: 700,
                    display: 'block',
                    marginBottom: 12,
                    color: '#1e293b',
                    fontSize: 14,
                  }}
                >
                  🔐 功能權限
                </label>
                {PERMISSIONS.map((perm, i) => (
                  <label
                    key={perm.key}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: 8,
                      borderRadius: 6,
                      background: 'white',
                      border: '1px solid #e2e8f0',
                      marginBottom: i < PERMISSIONS.length - 1 ? 8 : 0,
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={!!editing[perm.key]}
                      onChange={() => setEditing((v) => ({ ...v, [perm.key]: !v[perm.key] }))}
                      style={{ width: 16, height: 16, accentColor: '#2e3f6e', cursor: 'pointer' }}
                    />
                    <span>
                      <strong style={{ display: 'block', fontSize: 13 }}>{perm.label}</strong>
                      <small style={{ color: '#64748b' }}>{perm.desc}</small>
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                gap: 10,
                marginTop: 0,
                flexShrink: 0,
                padding: '15px 0',
                borderTop: '1px solid #e2e8f0',
              }}
            >
              <button
                onClick={() => setModalOpen(false)}
                style={{
                  padding: '8px 18px',
                  border: '1.5px solid #cbd5e1',
                  borderRadius: 8,
                  background: 'white',
                  fontSize: 14,
                  cursor: 'pointer',
                  fontWeight: 600,
                  color: '#475569',
                }}
              >
                取消
              </button>
              <button
                onClick={saveRole}
                style={{
                  padding: '8px 22px',
                  background: '#2e3f6e',
                  color: 'white',
                  border: 'none',
                  borderRadius: 8,
                  fontSize: 14,
                  cursor: 'pointer',
                  fontWeight: 700,
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#1e2d52')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '#2e3f6e')}
              >
                儲存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
