import { useState } from 'react'

export default function TableTab({ kb }) {
  const [selectedTableId, setSelectedTableId] = useState(null)

  if (selectedTableId) {
    const table = kb.tables.find(t => t.id === selectedTableId)
    return (
      <div>
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-bold text-slate-800">{table.name}</h3>
          <button
            onClick={() => setSelectedTableId(null)}
            className="text-sm text-slate-500 font-semibold hover:text-slate-800"
          >
            ← 回列表
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-slate-200 text-sm">
            <thead>
              <tr>
                {table.columns.map(col => (
                  <th key={col} className="px-3 py-2.5 bg-slate-50 text-slate-700 font-bold border border-slate-200 text-left">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  {row.map((cell, j) => (
                    <td key={j} className="px-3 py-2.5 border border-slate-200 text-slate-600">{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <div>
          <span className="font-bold text-slate-800 text-sm">結構化資料表</span>
          <span className="text-xs text-slate-400 ml-2">可自訂建立或匯入 Excel/CSV</span>
        </div>
        <button className="px-3.5 py-1.5 bg-[#2e3f6e] text-white rounded-md text-sm font-semibold hover:bg-[#1e2d52] transition-colors">
          + 新增資料表
        </button>
      </div>
      <div className="grid gap-3">
        {kb.tables.map(table => (
          <div
            key={table.id}
            onClick={() => setSelectedTableId(table.id)}
            className="border border-slate-200 rounded-lg p-4 cursor-pointer hover:bg-slate-50 flex justify-between items-center transition-colors"
          >
            <div>
              <p className="font-semibold text-slate-800 text-sm">{table.name}</p>
              <p className="text-xs text-slate-400 mt-1">
                {table.columns.length} 欄 · {table.rows.length} 筆 · 建立 {table.createdDate}
              </p>
            </div>
            <span className="text-slate-400 text-sm">→</span>
          </div>
        ))}
      </div>
    </div>
  )
}
