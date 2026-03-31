import { useState } from 'react'
import { users as initialUsers } from '../../data/users'
import Modal from '../../components/ui/Modal'

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

  function toggleAllRoles() {
    setNewRoles((prev) => (prev.length === ROLE_OPTIONS.length ? [] : [...ROLE_OPTIONS]))
  }

  const filtered = userList.filter((u) => {
    if (applied.role !== 'all' && !u.roles.includes(applied.role)) return false
    if (applied.keyword) {
      const kw = applied.keyword.toLowerCase()
      if (!u.name.toLowerCase().includes(kw) && !u.email.toLowerCase().includes(kw)) return false
    }
    return true
  })

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-extrabold text-slate-800">帳號管理</h2>
        <button
          onClick={() => {
            setNewName('')
            setNewEmail('')
            setNewRoles([])
            setModalOpen(true)
          }}
          className="px-4 py-2 bg-[#2e3f6e] text-white rounded-lg text-sm font-bold hover:bg-[#1e2d52] transition-colors"
        >
          新增帳號
        </button>
      </div>

      {/* Filter bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-3 mb-4 flex gap-3 items-center flex-wrap">
        <label className="text-sm font-semibold whitespace-nowrap">角色職位:</label>
        <select
          value={filterRole}
          onChange={(e) => setFilterRole(e.target.value)}
          style={{
            height: 36,
            padding: '0 10px',
            border: '1px solid #cbd5e1',
            borderRadius: 6,
            fontSize: 13,
            outline: 'none',
          }}
        >
          <option value="all">全部</option>
          {ROLE_OPTIONS.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <label className="text-sm font-semibold whitespace-nowrap" style={{ marginLeft: 10 }}>
          關鍵字搜尋:
        </label>
        <input
          value={filterKeyword}
          onChange={(e) => setFilterKeyword(e.target.value)}
          placeholder="搜尋姓名或信箱..."
          style={{
            height: 36,
            padding: '0 10px',
            border: '1px solid #cbd5e1',
            borderRadius: 6,
            fontSize: 13,
            outline: 'none',
            flex: 1,
            minWidth: 160,
          }}
        />
        <button
          onClick={() => setApplied({ role: filterRole, keyword: filterKeyword })}
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

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              {['姓名', '電子信箱', '角色', '執行動作'].map((h) => (
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
            {filtered.map((user) => (
              <tr key={user.id} className="border-b border-slate-100">
                <td className="px-4 py-3.5 text-sm font-semibold text-slate-700">{user.name}</td>
                <td className="px-4 py-3.5 text-sm text-slate-500">{user.email}</td>
                <td className="px-4 py-3.5 text-sm text-slate-600">{user.roles.join('、')}</td>
                <td className="px-4 py-3.5">
                  <div className="flex gap-2">
                    <button className="text-sm font-semibold text-slate-500 border border-slate-300 px-3 py-1 rounded-md hover:bg-slate-50">
                      編輯
                    </button>
                    <button
                      onClick={() => setUserList((u) => u.filter((x) => x.id !== user.id))}
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

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title="新增帳號"
        footer={
          <>
            <button
              onClick={() => setModalOpen(false)}
              className="px-4 py-2 border border-slate-300 rounded-md text-sm font-semibold hover:bg-slate-50"
            >
              取消
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 bg-[#2e3f6e] text-white rounded-md text-sm font-bold hover:bg-[#1e2d52]"
            >
              儲存
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-600 mb-1.5">名稱</label>
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full px-3 py-2.5 border-2 border-slate-200 rounded-lg text-sm outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-600 mb-1.5">Email</label>
            <input
              type="email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              className="w-full px-3 py-2.5 border-2 border-slate-200 rounded-lg text-sm outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-sm font-semibold text-slate-600">角色</label>
              <button
                onClick={toggleAllRoles}
                style={{
                  fontSize: 12,
                  color: '#2e3f6e',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
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
              {ROLE_OPTIONS.map((r) => (
                <label
                  key={r}
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
                    checked={newRoles.includes(r)}
                    onChange={() => toggleRole(r)}
                    style={{ width: 15, height: 15, accentColor: '#2e3f6e' }}
                  />
                  <span style={{ fontSize: 13 }}>{r}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </Modal>
    </div>
  )
}
