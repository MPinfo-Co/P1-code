export default function AccessTab({ kb }) {
  return (
    <div>
      <h3 className="font-bold text-slate-800 text-sm mb-4">存取設定</h3>
      <p className="text-sm text-slate-500 mb-3">以下角色可存取此知識庫：</p>
      <div className="space-y-2">
        {kb.accessRoles.map((role) => (
          <div
            key={role}
            className="flex items-center justify-between border border-slate-200 rounded-lg px-4 py-3"
          >
            <span className="text-sm font-semibold text-slate-700">{role}</span>
            <button className="text-xs text-red-500 font-semibold hover:underline">移除</button>
          </div>
        ))}
      </div>
      <button className="mt-4 px-4 py-2 border-2 border-[#2e3f6e] text-[#2e3f6e] rounded-md text-sm font-semibold hover:bg-[#eef1f8] transition-colors">
        + 新增角色存取
      </button>
    </div>
  )
}
