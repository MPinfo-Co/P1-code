export default function Pagination({ current, total, onChange }) {
  if (total <= 1) return null
  return (
    <div className="flex justify-center gap-2 mt-5">
      {Array.from({ length: total }, (_, i) => i + 1).map(page => (
        <button
          key={page}
          onClick={() => onChange(page)}
          className={`px-3 py-1.5 border rounded-md text-sm font-medium transition-colors ${
            page === current
              ? 'bg-[#2e3f6e] text-white border-[#2e3f6e]'
              : 'bg-white border-slate-300 hover:bg-slate-50'
          }`}
        >
          {page}
        </button>
      ))}
    </div>
  )
}
