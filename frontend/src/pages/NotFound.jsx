import { Link } from 'react-router-dom'
export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-screen text-slate-500">
      <h1 className="text-6xl font-extrabold text-slate-300 mb-4">404</h1>
      <p className="mb-6">找不到這個頁面</p>
      <Link to="/" className="text-[#2e3f6e] font-semibold hover:underline">
        回首頁
      </Link>
    </div>
  )
}
