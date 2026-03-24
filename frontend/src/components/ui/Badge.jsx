const VARIANTS = {
  builtin: 'bg-slate-100 text-[#1e2d52] border border-[#c5ccdf]',
  new:     'bg-emerald-50 text-emerald-700 border border-emerald-400',
  status:  'bg-slate-100 text-slate-600 border border-slate-200',
  red:     'bg-red-50 text-red-600 border border-red-300',
  orange:  'bg-orange-50 text-orange-600 border border-orange-300',
}

export default function Badge({ variant = 'status', children }) {
  return (
    <span className={`inline-block text-[11px] font-bold px-1.5 py-0.5 rounded ml-2 ${VARIANTS[variant]}`}>
      {children}
    </span>
  )
}
