export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-slate-500">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" strokeWidth="1.5" className="mb-5">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
      <h2 className="text-3xl font-extrabold text-slate-800 mb-3">歡迎進入 MP-Box 管理中心</h2>
      <p>請使用左側目錄來操作功能。</p>
    </div>
  )
}
