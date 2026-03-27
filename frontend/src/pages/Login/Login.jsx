import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../stores/authStore'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-[#1e2d52] to-[#2e3f6e]">
      <div className="bg-white rounded-xl shadow-2xl p-12 w-full max-w-[430px] text-center">
        <h1 className="text-4xl font-black text-slate-800 mb-8">MP-Box</h1>
        <form onSubmit={handleSubmit} className="space-y-5 text-left">
          <div>
            <label className="block text-sm font-semibold text-slate-600 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg bg-slate-50 focus:border-indigo-500 outline-none"
              placeholder="輸入 Email"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-600 mb-2">密碼</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg bg-slate-50 focus:border-indigo-500 outline-none"
              placeholder="密碼"
              required
            />
          </div>
          {error && <p className="text-red-500 text-sm font-medium">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-[#2e3f6e] text-white rounded-lg text-base font-bold hover:bg-[#1e2d52] transition-colors disabled:opacity-60"
          >
            {loading ? '登入中...' : '登入系統'}
          </button>
        </form>
      </div>
    </div>
  )
}
