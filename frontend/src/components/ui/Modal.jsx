export default function Modal({ open, onClose, title, children, footer }) {
  if (!open) return null
  return (
    <div
      className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl p-8 w-full max-w-lg shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {title && <h3 className="text-lg font-bold text-slate-800 mb-5">{title}</h3>}
        {children}
        {footer && <div className="mt-6 flex justify-end gap-3">{footer}</div>}
      </div>
    </div>
  )
}
