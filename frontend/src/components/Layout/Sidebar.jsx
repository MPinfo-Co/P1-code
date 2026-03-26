// src/components/Layout/Sidebar.jsx
import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../stores/authStore'

export default function Sidebar() {
  const [settingOpen, setSettingOpen] = useState(false)
  const { user } = useAuth()
  const canSeeSetting = user?.role === '管理員'

  return (
    <aside className="w-64 bg-slate-900 text-slate-400 flex flex-col h-full">
      {/* Brand */}
      <NavLink
        to="/ai-partner"
        className="px-6 py-5 text-2xl font-extrabold text-white border-b border-slate-800 flex items-center gap-2"
      >
        MP-Box
      </NavLink>

      {/* Nav */}
      <ul className="flex-1 py-5">
        <li>
          <NavLink
            to="/ai-partner"
            className={({ isActive }) =>
              `flex items-center gap-3 px-6 py-3 font-medium transition-all ${
                isActive ? 'border-l-4 border-indigo-500 text-white bg-slate-800' : 'hover:text-white'
              }`
            }
          >
            <svg className="w-5 h-5 stroke-current fill-none" strokeWidth="1.5" viewBox="0 0 24 24">
              <rect x="4" y="8" width="16" height="12" rx="2" />
              <path d="M9 13h0M15 13h0" strokeWidth="3" strokeLinecap="round" />
              <path d="M12 2v4M2 12h2M20 12h2" />
            </svg>
            AI夥伴
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/kb"
            className={({ isActive }) =>
              `flex items-center gap-3 px-6 py-3 font-medium transition-all ${
                isActive ? 'border-l-4 border-indigo-500 text-white bg-slate-800' : 'hover:text-white'
              }`
            }
          >
            <svg className="w-5 h-5 stroke-current fill-none" strokeWidth="1.5" viewBox="0 0 24 24">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
            知識庫
          </NavLink>
        </li>
        {canSeeSetting && (
          <li>
            <button
              onClick={() => setSettingOpen((o) => !o)}
              className="w-full flex items-center gap-3 px-6 py-3 font-medium hover:text-white transition-all"
            >
              <svg className="w-5 h-5 stroke-current fill-none" strokeWidth="1.5" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
              設定 {settingOpen ? '▴' : '▾'}
            </button>
            <ul className={`nav-submenu bg-slate-950 ${settingOpen ? 'open' : ''}`}>
              <li>
                <NavLink to="/settings/account" className="block py-2.5 pl-14 text-sm hover:text-white">
                  帳號
                </NavLink>
              </li>
              <li>
                <NavLink to="/settings/role" className="block py-2.5 pl-14 text-sm hover:text-white">
                  角色
                </NavLink>
              </li>
              <li>
                <NavLink to="/settings/ai-config" className="block py-2.5 pl-14 text-sm hover:text-white">
                  AI夥伴管理
                </NavLink>
              </li>
            </ul>
          </li>
        )}
      </ul>

      <div className="px-6 py-3 text-xs text-slate-500 border-t border-slate-800">v73</div>
    </aside>
  )
}
