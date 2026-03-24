import { useState } from 'react'
import Pagination from '../../components/ui/Pagination'

const PAGE_SIZE = 5

export default function DocTab({ kb }) {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const filtered = kb.docs.filter(d => d.name.includes(search))
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <div>
          <span className="text-sm font-bold text-slate-800">非結構化文件</span>
          <span className="text-xs text-slate-400 ml-2">上傳 PDF / Word / TXT，系統自動進行向量化索引</span>
        </div>
        <button className="px-3.5 py-1.5 bg-[#2e3f6e] text-white rounded-md text-sm font-semibold hover:bg-[#1e2d52] transition-colors">
          ↑ 上傳文件
        </button>
      </div>
      <input
        value={search}
        onChange={e => { setSearch(e.target.value); setPage(1) }}
        placeholder="搜尋檔案名稱..."
        className="px-3 py-2 border border-slate-300 rounded-md text-sm outline-none w-64 mb-3"
      />
      <table className="w-full border-collapse">
        <thead>
          <tr>
            {['檔案名稱', '大小', '上傳日期', '操作'].map(h => (
              <th key={h} className="text-left px-3 py-3 bg-slate-50 text-slate-700 font-bold text-sm border-b-2 border-slate-200">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {paged.map(doc => (
            <tr key={doc.id} className="border-b border-slate-100 hover:bg-slate-50">
              <td className="px-3 py-3 text-sm text-slate-700">{doc.name}</td>
              <td className="px-3 py-3 text-sm text-slate-500">{doc.size}</td>
              <td className="px-3 py-3 text-sm text-slate-500">{doc.uploadDate}</td>
              <td className="px-3 py-3">
                <button className="text-xs text-red-500 font-semibold hover:underline">刪除</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <Pagination current={page} total={totalPages} onChange={setPage} />
    </div>
  )
}
