export default function Pagination({
  page,
  pageSize,
  total,
  totalPages: totalPagesProp = undefined,
  onPageChange,
}) {
  const totalPages = totalPagesProp ?? (pageSize > 0 ? Math.max(1, Math.ceil(total / pageSize)) : 1)
  if (totalPages <= 1) return null

  return (
    <div className="flex justify-center items-center gap-2 mt-5">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1}
        className={`px-3 py-1.5 border rounded-md text-sm font-medium transition-colors ${
          page === 1
            ? 'bg-white border-slate-200 text-slate-300 cursor-not-allowed'
            : 'bg-white border-slate-300 hover:bg-slate-50'
        }`}
      >
        上一頁
      </button>

      {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
        <button
          key={p}
          onClick={() => onPageChange(p)}
          className={`px-3 py-1.5 border rounded-md text-sm font-medium transition-colors ${
            p === page
              ? 'bg-[#2e3f6e] text-white border-[#2e3f6e] active'
              : 'bg-white border-slate-300 hover:bg-slate-50'
          }`}
        >
          {p}
        </button>
      ))}

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page === totalPages}
        className={`px-3 py-1.5 border rounded-md text-sm font-medium transition-colors ${
          page === totalPages
            ? 'bg-white border-slate-200 text-slate-300 cursor-not-allowed'
            : 'bg-white border-slate-300 hover:bg-slate-50'
        }`}
      >
        下一頁
      </button>
    </div>
  )
}
