// src/components/Layout/Header.jsx
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../stores/authStore'

const PAGE_TITLES = {
  '/': '首頁',
  '/ai-partner': 'AI夥伴',
  '/kb': '知識庫',
  '/settings/account': '帳號',
  '/settings/role': '角色',
  '/settings/ai-config': 'AI夥伴管理',
}

export default function Header() {
  const { logout } = useAuth()
  const { pathname } = useLocation()
  const navigate = useNavigate()

  // Find the most specific matching path
  const title =
    Object.entries(PAGE_TITLES)
      .filter(([path]) => pathname === path || pathname.startsWith(path + '/'))
      .sort((a, b) => b[0].length - a[0].length)[0]?.[1] ?? 'MP-Box'

  return (
    <header className="bg-white border-b border-slate-200 flex items-center justify-between px-8 h-[70px]">
      <h1 className="text-lg font-extrabold text-slate-900">{title}</h1>
      <button
        onClick={() => {
          logout()
          navigate('/login')
        }}
        className="text-red-500 font-semibold text-sm hover:text-red-700 transition-colors"
      >
        登出
      </button>
    </header>
  )
}
