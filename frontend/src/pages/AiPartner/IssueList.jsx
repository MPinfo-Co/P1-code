import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useIssues } from '../../contexts/IssuesContext'
import Pagination from '../../components/ui/Pagination'

const PAGE_SIZE = 10

const STAR_COLOR = { 5: '#b91c1c', 4: '#c2410c', 3: '#b45309', 2: '#1e40af', 1: '#475569' }

function StarRank({ rank }) {
  const color = STAR_COLOR[rank] || '#475569'
  return (
    <span style={{ whiteSpace: 'nowrap' }}>
      <span style={{ color, fontSize: 15, letterSpacing: 1 }}>{'★'.repeat(rank)}</span>
      <span style={{ color: '#e2e8f0', fontSize: 15, letterSpacing: 1 }}>
        {'★'.repeat(5 - rank)}
      </span>
    </span>
  )
}

function StatusIcon({ status }) {
  if (status === '未處理')
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    )
  if (status === '處理中')
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2">
        <polyline points="23 4 23 10 17 10" />
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
      </svg>
    )
  if (status === '已完成')
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    )
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2">
      <rect x="6" y="4" width="4" height="16" />
      <rect x="14" y="4" width="4" height="16" />
    </svg>
  )
}

function AffectedPopover({ issue }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function handler(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [])

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <div
        onClick={(e) => {
          e.stopPropagation()
          setOpen((v) => !v)
        }}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 5,
          padding: '3px 9px',
          borderRadius: 5,
          fontSize: 12,
          fontWeight: 600,
          background: '#f1f5f9',
          color: '#475569',
          border: '1px solid #e2e8f0',
          cursor: 'pointer',
          whiteSpace: 'nowrap',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = '#e2e8f0'
          e.currentTarget.style.borderColor = '#94a3b8'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = '#f1f5f9'
          e.currentTarget.style.borderColor = '#e2e8f0'
        }}
      >
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <rect x="2" y="3" width="20" height="14" rx="2" />
          <path d="M8 21h8M12 17v4" />
        </svg>
        {issue.affectedSummary}
        <svg
          width="11"
          height="11"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </div>
      {open && (
        <div
          style={{
            display: 'block',
            position: 'absolute',
            top: 'calc(100% + 6px)',
            left: 0,
            zIndex: 200,
            background: 'white',
            border: '1px solid #cbd5e1',
            borderRadius: 8,
            padding: '12px 14px',
            minWidth: 280,
            maxWidth: 420,
            boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
            fontSize: 13,
            color: '#334155',
            lineHeight: 1.6,
            whiteSpace: 'normal',
          }}
        >
          <div
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: '#94a3b8',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
              marginBottom: 6,
            }}
          >
            完整影響範圍
          </div>
          {issue.affected}
        </div>
      )}
    </div>
  )
}

export default function IssueList() {
  const { partnerId } = useParams()
  const navigate = useNavigate()
  const { issues } = useIssues()

  const [filterStatus, setFilterStatus] = useState('all')
  const [filterStart, setFilterStart] = useState('')
  const [filterEnd, setFilterEnd] = useState('')
  const [filterKeyword, setFilterKeyword] = useState('')
  const [applied, setApplied] = useState({ status: 'all', start: '', end: '', keyword: '' })
  const [page, setPage] = useState(1)

  function applyFilters() {
    setApplied({ status: filterStatus, start: filterStart, end: filterEnd, keyword: filterKeyword })
    setPage(1)
  }

  function resetFilters() {
    setFilterStatus('all')
    setFilterStart('')
    setFilterEnd('')
    setFilterKeyword('')
    setApplied({ status: 'all', start: '', end: '', keyword: '' })
    setPage(1)
  }

  const kw = applied.keyword.toLowerCase().replace(/\s+/g, '')
  const partnerIssues = issues.filter((i) => i.partnerId === partnerId)
  const filtered = partnerIssues
    .filter((i) => {
      if (applied.status !== 'all' && i.currentStatus !== applied.status) return false
      if (applied.keyword) {
        const fields = [i.title, i.affected, i.currentStatus, i.date, i.desc, String(i.starRank)]
        const match = fields.some((f) => {
          const t = (f || '').toLowerCase()
          return t.includes(applied.keyword.toLowerCase()) || t.replace(/\s+/g, '').includes(kw)
        })
        if (!match) return false
      }
      if (applied.start && i.date < applied.start) return false
      if (applied.end && i.date > applied.end) return false
      return true
    })
    .sort((a, b) => b.starRank - a.starRank)

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  function getAssignee(issue) {
    if (issue.history && issue.history.length > 0)
      return issue.history[issue.history.length - 1].user
    return null
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 110px)' }}>
      <div className="flex justify-between items-center mb-4 flex-shrink-0">
        <h2 className="text-xl font-extrabold text-slate-800">安全事件清單</h2>
        <button
          onClick={() => navigate('/ai-partner')}
          className="flex items-center gap-1.5 px-3 py-2 border border-slate-300 bg-white text-slate-600 rounded-md text-sm font-semibold hover:bg-slate-50"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
          回上一頁
        </button>
      </div>

      {/* Filter bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4 flex-shrink-0 flex flex-wrap gap-3 items-center">
        <label className="font-semibold text-sm whitespace-nowrap">處理狀態:</label>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          style={{
            height: 36,
            padding: '0 10px',
            border: '1px solid #cbd5e1',
            borderRadius: 6,
            fontSize: 13,
            outline: 'none',
            minWidth: 90,
          }}
        >
          <option value="all">全部</option>
          {['未處理', '處理中', '已完成', '擱置'].map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <label className="text-sm whitespace-nowrap">發生日期:</label>
        <input
          type="date"
          value={filterStart}
          onChange={(e) => setFilterStart(e.target.value)}
          style={{
            height: 36,
            padding: '0 10px',
            border: '1px solid #cbd5e1',
            borderRadius: 6,
            fontSize: 13,
            outline: 'none',
            boxSizing: 'border-box',
          }}
        />
        <span className="text-sm">至</span>
        <input
          type="date"
          value={filterEnd}
          onChange={(e) => setFilterEnd(e.target.value)}
          style={{
            height: 36,
            padding: '0 10px',
            border: '1px solid #cbd5e1',
            borderRadius: 6,
            fontSize: 13,
            outline: 'none',
            boxSizing: 'border-box',
          }}
        />
        <label className="text-sm whitespace-nowrap">關鍵字:</label>
        <input
          type="text"
          value={filterKeyword}
          onChange={(e) => setFilterKeyword(e.target.value)}
          placeholder="搜尋事件說明、狀態..."
          style={{
            height: 36,
            padding: '0 12px',
            border: '1px solid #cbd5e1',
            borderRadius: 6,
            fontSize: 13,
            outline: 'none',
            boxSizing: 'border-box',
            width: 200,
          }}
        />
        <button
          onClick={applyFilters}
          style={{
            padding: '8px 16px',
            borderRadius: 6,
            cursor: 'pointer',
            fontWeight: 600,
            border: '1.5px solid #2e3f6e',
            background: 'white',
            color: '#2e3f6e',
            fontSize: 13.5,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = '#eef1f8')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
        >
          套用
        </button>
        <button
          onClick={resetFilters}
          className="px-4 py-2 border border-slate-300 bg-white text-slate-700 rounded-md text-sm font-semibold hover:bg-slate-50"
        >
          重設
        </button>
      </div>

      {/* Table */}
      <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
        <div
          style={{ height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}
        >
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden flex-shrink-0">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  {[
                    '事件說明',
                    '處理優先級',
                    '發生日期區間',
                    '影響範圍',
                    '處理狀態',
                    '負責人員',
                    '執行動作',
                  ].map((h) => (
                    <th
                      key={h}
                      className="text-left px-4 py-3.5 bg-slate-100 text-slate-800 font-extrabold text-sm border-b-2 border-slate-300"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {paged.map((issue) => (
                  <tr
                    key={issue.id}
                    className="border-b border-slate-200 hover:bg-slate-50 transition-colors cursor-pointer"
                    onClick={() => navigate(`/ai-partner/${partnerId}/issues/${issue.id}`)}
                  >
                    <td className="px-4 py-3.5 text-sm font-semibold text-slate-700 max-w-xs">
                      <span className="line-clamp-2">{issue.title}</span>
                    </td>
                    <td className="px-4 py-3.5 whitespace-nowrap">
                      <StarRank rank={issue.starRank} />
                    </td>
                    <td className="px-4 py-3.5 text-sm text-slate-600 whitespace-nowrap">
                      {issue.dateEnd && issue.dateEnd !== issue.date
                        ? `${issue.date} ~ ${issue.dateEnd}`
                        : issue.date}
                    </td>
                    <td className="px-4 py-3.5">
                      <AffectedPopover issue={issue} />
                    </td>
                    <td className="px-4 py-3.5 text-sm">
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 6,
                          fontSize: 13,
                          fontWeight: 500,
                          color: '#334155',
                        }}
                      >
                        <StatusIcon status={issue.currentStatus} />
                        {issue.currentStatus}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-sm text-slate-600">
                      {getAssignee(issue) ?? <span className="text-slate-400">未指派</span>}
                    </td>
                    <td className="px-4 py-3.5">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/ai-partner/${partnerId}/issues/${issue.id}`)
                        }}
                        className="px-3 py-1.5 bg-[#2e3f6e] text-white rounded-md text-xs font-semibold hover:bg-[#1e2d52]"
                      >
                        事件處理
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination current={page} total={totalPages} onChange={setPage} />
        </div>
      </div>
    </div>
  )
}
