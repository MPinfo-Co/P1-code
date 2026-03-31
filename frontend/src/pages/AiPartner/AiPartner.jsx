// src/pages/AiPartner/AiPartner.jsx
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { aiPartners } from '../../data/aiPartners'
import Badge from '../../components/ui/Badge'

export default function AiPartner() {
  const [keyword, setKeyword] = useState('')
  const navigate = useNavigate()

  const filtered = aiPartners.filter(
    (p) => p.name.includes(keyword) || p.description?.includes(keyword)
  )

  return (
    <div>
      <h2 className="text-xl font-extrabold text-slate-800 mb-4">選擇 AI 夥伴</h2>
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-5">
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium text-slate-600 whitespace-nowrap">
            關鍵字搜尋:
          </label>
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜尋 AI 夥伴名稱或說明..."
            className="flex-1 px-3 py-2 border border-slate-300 rounded-md text-sm outline-none focus:border-indigo-500"
          />
        </div>
      </div>
      <div
        className="grid gap-5"
        style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))' }}
      >
        {filtered.map((partner) => (
          <div
            key={partner.id}
            onClick={() => !partner.disabled && navigate(`/ai-partner/${partner.id}/issues`)}
            className={`bg-white rounded-xl border border-slate-200 p-8 text-center transition-all ${
              partner.disabled
                ? 'opacity-60 grayscale cursor-not-allowed'
                : 'cursor-pointer hover:-translate-y-1 hover:shadow-lg hover:border-slate-300'
            }`}
          >
            {partner.builtin ? (
              <svg
                className="w-12 h-12 mx-auto mb-4 stroke-[#2e3f6e] fill-none"
                strokeWidth="1.5"
                viewBox="0 0 24 24"
              >
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="M12 8v4" />
                <path d="M12 16h.01" />
              </svg>
            ) : (
              <svg
                className="w-12 h-12 mx-auto mb-4 fill-none"
                strokeWidth="1.5"
                viewBox="0 0 24 24"
                stroke={partner.disabled ? '#94a3b8' : '#2e3f6e'}
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            )}
            <h3 className="text-slate-800 font-bold text-base">
              {partner.name}
              <Badge variant={partner.builtin ? 'builtin' : 'new'}>
                {partner.builtin ? '預設' : '自訂'}
              </Badge>
            </h3>
            {partner.disabled ? (
              <p className="text-red-500 font-bold mt-3 text-sm">● 停用中</p>
            ) : (
              <p className="text-slate-500 text-sm mt-3">{partner.description}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
