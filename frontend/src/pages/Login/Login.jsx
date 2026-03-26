import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../stores/authStore'
import { users } from '../../data/users'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    // Mock auth: username (name/email) + password "123"
    const uLower = username.toLowerCase()
    const found = users.find(u => u.name.toLowerCase() === uLower || u.email.toLowerCase() === uLower ||
      u.name.toLowerCase().split(' ')[0] === uLower)
    if (found && password === '123') {
      login(found.name, found.roles[0])
      navigate('/')
    } else {
      setError('帳號或密碼錯誤')
    }
  }

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-[#1e2d52] to-[#2e3f6e]">
      <div className="bg-white rounded-xl shadow-2xl p-12 w-full max-w-[430px] text-center">
        <h1 className="text-4xl font-black text-slate-800 mb-8">MP-Box</h1>
        <form onSubmit={handleSubmit} className="space-y-5 text-left">
          <div>
            <label className="block text-sm font-semibold text-slate-600 mb-2">帳號</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg bg-slate-50 focus:border-indigo-500 outline-none"
              placeholder="輸入姓名或 Email"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-600 mb-2">密碼</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg bg-slate-50 focus:border-indigo-500 outline-none"
              placeholder="密碼（mock: 123）"
            />
          </div>
          {error && <p className="text-red-500 text-sm font-medium">{error}</p>}
          <button
            type="submit"
            className="w-full py-3.5 bg-[#2e3f6e] text-white rounded-lg text-base font-bold hover:bg-[#1e2d52] transition-colors"
          >
            登入系統
          </button>
        </form>
      </div>
    </div>
  )
}
