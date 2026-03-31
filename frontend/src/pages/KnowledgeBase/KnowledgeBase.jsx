import { useState } from 'react'
import { knowledgeBases } from '../../data/knowledgeBase'
import DocTab from './DocTab'
import TableTab from './TableTab'
import AccessTab from './AccessTab'

export default function KnowledgeBase() {
  const [keyword, setKeyword] = useState('')
  const [selectedKbId, setSelectedKbId] = useState(null)
  const [activeTab, setActiveTab] = useState('docs')

  const filtered = knowledgeBases.filter(
    (kb) => kb.name.includes(keyword) || kb.desc.includes(keyword)
  )

  if (selectedKbId !== null) {
    const kb = knowledgeBases.find((k) => k.id === selectedKbId)
    const tabs = [
      { id: 'docs', label: '文件' },
      { id: 'tables', label: '資料表' },
      { id: 'access', label: '存取設定' },
    ]
    return (
      <div>
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 stroke-slate-500 fill-none" strokeWidth="2" viewBox="0 0 24 24">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
            <h2 className="text-xl font-extrabold text-slate-800">{kb.name}</h2>
          </div>
          <button
            onClick={() => setSelectedKbId(null)}
            className="flex items-center gap-1.5 text-slate-500 font-semibold text-sm hover:text-slate-800"
          >
            ← 回知識庫列表
          </button>
        </div>
        <p className="text-sm text-slate-500 mb-1">{kb.desc}</p>
        <p className="text-xs text-[#2e3f6e] font-semibold mb-5">
          綁定夥伴：{kb.boundPartners.join('、')}
        </p>

        {/* Tab nav */}
        <div className="flex border border-slate-200 rounded-t-lg overflow-hidden">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 text-sm font-semibold border-r border-slate-200 last:border-r-0 transition-all ${
                activeTab === tab.id
                  ? 'bg-white text-[#2e3f6e] border-b-2 border-b-[#2e3f6e]'
                  : 'bg-slate-50 text-slate-500 hover:bg-slate-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="border border-slate-200 border-t-0 rounded-b-lg bg-white p-5">
          {activeTab === 'docs' && <DocTab kb={kb} />}
          {activeTab === 'tables' && <TableTab kb={kb} />}
          {activeTab === 'access' && <AccessTab kb={kb} />}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-extrabold text-slate-800">知識庫</h2>
        <button className="px-4 py-2 bg-[#2e3f6e] text-white rounded-lg text-sm font-bold hover:bg-[#1e2d52] transition-colors">
          + 新增知識庫
        </button>
      </div>
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-5">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-slate-600 whitespace-nowrap">
            關鍵字搜尋:
          </label>
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜尋知識庫名稱或說明..."
            className="flex-1 px-3 py-2 border border-slate-300 rounded-md text-sm outline-none"
          />
        </div>
      </div>
      <div
        className="grid gap-5"
        style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}
      >
        {filtered.map((kb) => (
          <div
            key={kb.id}
            onClick={() => {
              setSelectedKbId(kb.id)
              setActiveTab('docs')
            }}
            className="bg-white rounded-xl border border-slate-200 p-8 cursor-pointer hover:-translate-y-1 hover:shadow-lg transition-all text-center"
          >
            <svg
              className="w-12 h-12 mx-auto mb-4 stroke-[#2e3f6e] fill-none"
              strokeWidth="1.5"
              viewBox="0 0 24 24"
            >
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
            <h3 className="text-slate-800 font-bold">{kb.name}</h3>
            <p className="text-slate-500 text-sm mt-2">{kb.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
