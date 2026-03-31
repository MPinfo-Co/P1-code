import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useIssues } from '../../contexts/IssuesContext'
import { suggestRefs, suggestUrgency } from '../../data/issues'
import { similarCasesData, getMockReply, getStepReply } from '../../data/mockKnowledge'

// ── helpers ──────────────────────────────────────────────

function formatDesc(text) {
  if (!text) return null
  const segments = text.split(/(?=【)/)
  return segments.map((seg, i) => {
    if (!seg) return null
    const m = seg.match(/^【([^\]】]+)】([\s\S]*)$/)
    if (m) {
      return (
        <div key={i} style={{ marginBottom: 12 }}>
          <div
            style={{
              fontWeight: 800,
              fontSize: 13,
              color: '#1e293b',
              marginBottom: 4,
              letterSpacing: 0.3,
            }}
          >
            【{m[1]}】
          </div>
          <div
            style={{
              paddingLeft: 14,
              borderLeft: '2px solid #e2e8f0',
              color: '#334155',
              fontSize: 13,
              lineHeight: 1.75,
              whiteSpace: 'pre-wrap',
            }}
          >
            {m[2].trim()}
          </div>
        </div>
      )
    }
    return (
      <div
        key={i}
        style={{
          fontSize: 13,
          color: '#334155',
          lineHeight: 1.75,
          marginBottom: 8,
          whiteSpace: 'pre-wrap',
        }}
      >
        {seg.trim()}
      </div>
    )
  })
}

function StatusIcon({ status, size = 14 }) {
  if (status === '未處理')
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="#ef4444"
        strokeWidth="2"
      >
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    )
  if (status === '處理中')
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="#f59e0b"
        strokeWidth="2"
      >
        <polyline points="23 4 23 10 17 10" />
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
      </svg>
    )
  if (status === '已完成')
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="#10b981"
        strokeWidth="2"
      >
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    )
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="#94a3b8"
      strokeWidth="2"
    >
      <rect x="6" y="4" width="4" height="16" />
      <rect x="14" y="4" width="4" height="16" />
    </svg>
  )
}

function Section({ title, icon, children }) {
  return (
    <div
      style={{ border: '1px solid #e2e8f0', borderRadius: 8, marginBottom: 16, overflow: 'hidden' }}
    >
      <div
        style={{
          background: '#f8fafc',
          padding: '12px 16px',
          borderBottom: '1px solid #e2e8f0',
          fontWeight: 700,
          color: '#1e293b',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          fontSize: 15,
        }}
      >
        {icon}
        {title}
      </div>
      <div
        style={{
          padding: 16,
          background: 'white',
          fontSize: 14,
          color: '#334155',
          lineHeight: 1.6,
        }}
      >
        {children}
      </div>
    </div>
  )
}

const URGENCY_STYLE = {
  最推薦: { background: '#eef1f8', color: '#2e3f6e', border: '1px solid #c5ccdf' },
  次推薦: { background: '#f8fafc', color: '#475569', border: '1px solid #cbd5e1' },
  可選: { background: '#f8fafc', color: '#94a3b8', border: '1px solid #e2e8f0' },
}

const OUTCOME_STYLE = {
  已完成: { background: '#f0fdf4', color: '#166534', border: '1px solid #bbf7d0' },
  擱置: { background: '#f8fafc', color: '#475569', border: '1px solid #cbd5e1' },
  已緩解: { background: '#fffbeb', color: '#b45309', border: '1px solid #fde68a' },
}

const HISTORY_BADGE = {
  已完成: 'color:#166534;background:#f0fdf4;border:1px solid #bbf7d0;',
  處理中: 'color:#b45309;background:#fffbeb;border:1px solid #fde68a;',
  擱置: 'color:#475569;background:#f8fafc;border:1px solid #cbd5e1;',
  未處理: 'color:#dc2626;background:#fef2f2;border:1px solid #fecaca;',
}

function nowDT() {
  return new Date().toISOString().slice(0, 16)
}

// ── Main Component ────────────────────────────────────────

export default function IssueDetail() {
  const { partnerId, issueId } = useParams()
  const navigate = useNavigate()
  const { issues, updateIssue } = useIssues()

  const issue = issues.find((i) => i.id === Number(issueId))

  const [activeTab, setActiveTab] = useState('detail')
  const [showAllLogs, setShowAllLogs] = useState(false)
  const [chatVisible, setChatVisible] = useState(true)
  const [chatMsgs, setChatMsgs] = useState([
    {
      role: 'assistant',
      content:
        '您好，有任何關於此安全事件的疑問，例如詳細處理步驟、技術背景或風險評估，都可以直接詢問。',
    },
  ])
  const [chatInput, setChatInput] = useState('')
  const chatEndRef = useRef(null)

  // history form
  const [histDate, setHistDate] = useState(nowDT)
  const [histNote, setHistNote] = useState('')
  const [histStatus, setHistStatus] = useState('')

  // resolution form
  const [resHandler, setResHandler] = useState('')
  const [resTime, setResTime] = useState(nowDT)
  const [resText, setResText] = useState('')

  // reset chat when issueId changes
  useEffect(() => {
    setChatMsgs([
      {
        role: 'assistant',
        content:
          '您好，有任何關於此安全事件的疑問，例如詳細處理步驟、技術背景或風險評估，都可以直接詢問。',
      },
    ])
    setActiveTab('detail')
    setShowAllLogs(false)
    setChatVisible(true)
    if (issue) {
      setHistStatus(issue.currentStatus)
      setResText(issue.resolution || '')
    }
  }, [issueId])

  useEffect(() => {
    if (issue) setHistStatus(issue.currentStatus)
  }, [issue?.currentStatus])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMsgs])

  if (!issue) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-400">
        <p className="text-lg font-semibold">找不到此事件</p>
        <button
          onClick={() => navigate(-1)}
          className="mt-4 text-[#2e3f6e] text-sm font-semibold hover:underline"
        >
          ← 返回
        </button>
      </div>
    )
  }

  const stepRefs = suggestRefs[issue.id] || []
  const stepUrgency = suggestUrgency[issue.id] || []
  const assignee =
    issue.history?.length > 0 ? issue.history[issue.history.length - 1].user : '未指派'
  const similarCases = similarCasesData[issue.id] || []
  const showResolution = issue.currentStatus === '已完成'

  // ── actions ──

  function addHistoryEntry() {
    if (!histNote.trim()) {
      alert('請輸入備註內容')
      return
    }
    const actualStatusChange = histStatus !== issue.currentStatus ? histStatus : null
    const noteText = actualStatusChange
      ? histNote + `　【狀態變更為：${actualStatusChange}】`
      : histNote
    const entry = {
      date: histDate.replace('T', ' '),
      user: '系統使用者',
      note: noteText,
      statusChange: actualStatusChange,
    }
    updateIssue(issue.id, (i) => ({
      history: [...(i.history || []), entry],
      currentStatus: actualStatusChange || i.currentStatus,
    }))
    setHistNote('')
    setHistDate(nowDT())
  }

  function deleteHistoryEntry(idx) {
    if (!window.confirm('確定要刪除此筆紀錄？')) return
    updateIssue(issue.id, (i) => {
      const history = i.history.filter((_, j) => j !== idx)
      let currentStatus = i.currentStatus
      const lastChange = [...history].reverse().find((h) => h.statusChange)
      if (lastChange) currentStatus = lastChange.statusChange
      else if (history.length > 0) currentStatus = '處理中'
      else currentStatus = '未處理'
      return { history, currentStatus }
    })
  }

  function saveResolution() {
    updateIssue(issue.id, () => ({
      resolution: resText,
      resolutionHandler: resHandler,
      resolutionTime: resTime,
    }))
    alert('結案說明已儲存')
  }

  function sendMsg(content) {
    const userMsg = content || chatInput.trim()
    if (!userMsg) return
    setChatInput('')
    setChatMsgs((prev) => [...prev, { role: 'user', content: userMsg }, { role: 'typing' }])
    setTimeout(() => {
      const reply = getMockReply(userMsg, issue, issues)
      setChatMsgs((prev) =>
        prev.filter((m) => m.role !== 'typing').concat({ role: 'assistant', content: reply })
      )
    }, 400)
  }

  function sendQuickChat(type) {
    const labelMap = {
      整體摘要: '整體事件摘要',
      相關發現: 'IOC 與相關發現',
      補充說明: '技術背景補充',
      修復建議: '完整修復建議',
    }
    const userMsg = `【${labelMap[type] || type}】`
    setChatMsgs((prev) => [...prev, { role: 'user', content: userMsg }, { role: 'typing' }])
    setTimeout(() => {
      const reply = getMockReply(type, issue, issues)
      setChatMsgs((prev) =>
        prev.filter((m) => m.role !== 'typing').concat({ role: 'assistant', content: reply })
      )
    }, 400)
  }

  function askSuggestStep(stepIdx) {
    const userMsg = `請說明「${issue.suggests[stepIdx]}」的詳細操作步驟`
    setChatMsgs((prev) => [...prev, { role: 'user', content: userMsg }, { role: 'typing' }])
    setTimeout(() => {
      const reply = getStepReply(issue, stepIdx)
      setChatMsgs((prev) =>
        prev.filter((m) => m.role !== 'typing').concat({ role: 'assistant', content: reply })
      )
    }, 400)
  }

  // ── render ──

  const tabs = [
    {
      id: 'detail',
      label: '事件詳情',
      icon: (
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
      ),
    },
    {
      id: 'similar',
      label: '歷史事件',
      icon: (
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      ),
    },
    {
      id: 'diary',
      label: '處置紀錄',
      icon: (
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      ),
    },
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 110px)' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 15,
          flexShrink: 0,
        }}
      >
        <h2 style={{ color: '#1e293b', fontSize: 18, fontWeight: 800 }}>{issue.title}</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <label
              style={{ fontSize: 13, color: '#475569', fontWeight: 600, whiteSpace: 'nowrap' }}
            >
              處理狀態:
            </label>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '6px 12px',
                border: '1.5px solid #e2e8f0',
                borderRadius: 6,
                background: '#f8fafc',
                minWidth: 100,
              }}
            >
              <StatusIcon status={issue.currentStatus} />
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                {issue.currentStatus}
              </span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <label
              style={{ fontSize: 13, color: '#475569', fontWeight: 600, whiteSpace: 'nowrap' }}
            >
              負責人員:
            </label>
            <span
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: '#1e293b',
                padding: '6px 12px',
                border: '1.5px solid #e2e8f0',
                borderRadius: 6,
                background: '#f8fafc',
                minWidth: 80,
              }}
            >
              {assignee}
            </span>
          </div>
          <button
            onClick={() => navigate(`/ai-partner/${partnerId}/issues`)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 14px',
              border: '1px solid #cbd5e1',
              background: 'white',
              borderRadius: 6,
              fontSize: 13.5,
              fontWeight: 600,
              cursor: 'pointer',
              color: '#334155',
            }}
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
      </div>

      {/* Two-column body */}
      <div style={{ display: 'flex', gap: 20, flex: 1, overflow: 'hidden', minHeight: 0 }}>
        {/* Left: Tabs */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            overflow: 'hidden',
            paddingRight: 4,
          }}
        >
          {/* Tab nav */}
          <div
            style={{
              display: 'flex',
              borderBottom: '2px solid #e2e8f0',
              marginBottom: 0,
              flexShrink: 0,
              background: 'white',
              borderRadius: '8px 8px 0 0',
              overflow: 'hidden',
              border: '1px solid #e2e8f0',
              borderBottomColor: 'transparent',
            }}
          >
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '11px 18px',
                  fontSize: 13,
                  fontWeight: 600,
                  color: activeTab === tab.id ? '#2e3f6e' : '#64748b',
                  background: activeTab === tab.id ? 'white' : '#f8fafc',
                  border: 'none',
                  cursor: 'pointer',
                  borderBottom: `2px solid ${activeTab === tab.id ? '#2e3f6e' : 'transparent'}`,
                  borderRight: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 7,
                  whiteSpace: 'nowrap',
                  transition: 'all 0.2s',
                }}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab panels */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: 16,
              background: 'white',
              border: '1px solid #e2e8f0',
              borderTop: 'none',
              borderRadius: '0 0 8px 8px',
              minHeight: 0,
            }}
          >
            {/* Tab 1: 事件詳情 */}
            {activeTab === 'detail' && (
              <div>
                <Section
                  title="事件摘要"
                  icon={
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="#2e3f6e"
                      strokeWidth="2"
                    >
                      <circle cx="12" cy="12" r="10" />
                      <line x1="12" y1="16" x2="12" y2="12" />
                      <line x1="12" y1="8" x2="12.01" y2="8" />
                    </svg>
                  }
                >
                  {formatDesc(issue.desc)}
                </Section>

                <Section
                  title="建議處置方法"
                  icon={
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="#94a3b8"
                      strokeWidth="2"
                    >
                      <polyline points="9 11 12 14 22 4" />
                      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                    </svg>
                  }
                >
                  {issue.suggests.map((s, idx) => {
                    const refs = stepRefs[idx] || []
                    const urg = stepUrgency[idx] || ''
                    return (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          gap: 0,
                          alignItems: 'flex-start',
                          padding: '9px 0',
                          borderBottom: '1px solid #f1f5f9',
                        }}
                      >
                        <div style={{ flexShrink: 0, width: 58, paddingTop: 2 }}>
                          {urg && (
                            <span
                              style={{
                                display: 'inline-block',
                                fontSize: 11,
                                fontWeight: 700,
                                padding: '1px 7px',
                                borderRadius: 4,
                                marginRight: 7,
                                verticalAlign: 'middle',
                                whiteSpace: 'nowrap',
                                ...URGENCY_STYLE[urg],
                              }}
                            >
                              {urg}
                            </span>
                          )}
                        </div>
                        <div
                          style={{
                            flex: 1,
                            minWidth: 0,
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: 10,
                          }}
                        >
                          <div
                            style={{
                              flex: 1,
                              fontSize: 13,
                              color: '#334155',
                              lineHeight: 1.65,
                              paddingTop: 1,
                            }}
                          >
                            {s}
                            {refs.length > 0 && (
                              <span
                                style={{
                                  display: 'inline-flex',
                                  flexWrap: 'wrap',
                                  gap: 4,
                                  marginLeft: 6,
                                  verticalAlign: 'middle',
                                }}
                              >
                                {refs.map((r, ri) => (
                                  <a
                                    key={ri}
                                    href={r.url}
                                    target="_blank"
                                    rel="noreferrer"
                                    style={{
                                      display: 'inline-flex',
                                      alignItems: 'center',
                                      gap: 2,
                                      padding: '2px 7px',
                                      borderRadius: 4,
                                      textDecoration: 'none',
                                      fontSize: 11,
                                      fontWeight: 700,
                                      background: '#f8f8f8',
                                      border: '1px solid #d1d5db',
                                      color: '#374151',
                                    }}
                                  >
                                    {r.label}
                                    {r.type === 'mitre' && r.name && (
                                      <span
                                        style={{ fontSize: 10, color: '#9ca3af', marginLeft: 2 }}
                                      >
                                        {r.name}
                                      </span>
                                    )}
                                    <svg
                                      width="8"
                                      height="8"
                                      viewBox="0 0 24 24"
                                      fill="none"
                                      stroke="currentColor"
                                      strokeWidth="2.5"
                                      style={{ marginLeft: 2, opacity: 0.5 }}
                                    >
                                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                                      <polyline points="15 3 21 3 21 9" />
                                      <line x1="10" y1="14" x2="21" y2="3" />
                                    </svg>
                                  </a>
                                ))}
                              </span>
                            )}
                          </div>
                          <div style={{ flexShrink: 0, paddingTop: 1 }}>
                            <button
                              onClick={() => askSuggestStep(idx)}
                              style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 3,
                                padding: '2px 8px',
                                borderRadius: 4,
                                border: '1px solid #2e3f6e',
                                background: 'white',
                                color: '#2e3f6e',
                                fontSize: 11,
                                fontWeight: 700,
                                cursor: 'pointer',
                                transition: 'all 0.15s',
                              }}
                              onMouseEnter={(e) => (e.currentTarget.style.background = '#eef1f8')}
                              onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
                            >
                              <svg
                                width="11"
                                height="11"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                              >
                                <rect x="4" y="8" width="16" height="12" rx="2" />
                                <path d="M9 13h0M15 13h0" strokeWidth="3" strokeLinecap="round" />
                                <path d="M12 2v4M2 12h2M20 12h2" />
                              </svg>
                              參考步驟
                            </button>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </Section>

                <Section
                  title="關聯日誌摘要"
                  icon={
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="#475569"
                      strokeWidth="2"
                    >
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                  }
                >
                  <div style={{ background: '#f8fafc' }}>
                    {issue.logs.slice(0, 3).map((log, i) => (
                      <div
                        key={i}
                        style={{
                          background: '#0f172a',
                          color: '#a5b4fc',
                          padding: 12,
                          borderRadius: 6,
                          fontFamily: 'monospace',
                          fontSize: 13,
                          lineHeight: 1.5,
                          whiteSpace: 'pre-wrap',
                          marginBottom: 5,
                        }}
                      >
                        {log}
                      </div>
                    ))}
                    {showAllLogs &&
                      issue.logs.slice(3).map((log, i) => (
                        <div
                          key={i + 3}
                          style={{
                            background: '#0f172a',
                            color: '#a5b4fc',
                            padding: 12,
                            borderRadius: 6,
                            fontFamily: 'monospace',
                            fontSize: 13,
                            lineHeight: 1.5,
                            whiteSpace: 'pre-wrap',
                            marginBottom: 5,
                            marginTop: 5,
                          }}
                        >
                          {log}
                        </div>
                      ))}
                    {issue.logs.length > 3 && (
                      <button
                        onClick={() => setShowAllLogs((v) => !v)}
                        style={{
                          marginTop: 10,
                          fontSize: 12,
                          padding: '4px 10px',
                          border: '1px solid #cbd5e1',
                          background: 'white',
                          borderRadius: 6,
                          cursor: 'pointer',
                          fontWeight: 600,
                        }}
                      >
                        {showAllLogs ? 'Less...' : `顯示完整關聯日誌 (More...)`}
                      </button>
                    )}
                  </div>
                </Section>
              </div>
            )}

            {/* Tab 2: 歷史事件 */}
            {activeTab === 'similar' && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#94a3b8"
                    strokeWidth="2"
                  >
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                  <span style={{ fontSize: 14, fontWeight: 700, color: '#1e293b' }}>歷史事件</span>
                </div>
                <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 14, paddingLeft: 24 }}>
                  相似度由 PRO 模型依據事件描述語意、MITRE
                  技術重疊度、影響設備類型自動計算，於每日分析時寫入。目前顯示為 mock 示意資料。
                </div>
                {similarCases.length === 0 ? (
                  <div
                    style={{
                      textAlign: 'center',
                      padding: '30px 0',
                      color: '#94a3b8',
                      fontSize: 13,
                    }}
                  >
                    <svg
                      width="40"
                      height="40"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="#cbd5e1"
                      strokeWidth="1.5"
                      style={{
                        marginBottom: 10,
                        display: 'block',
                        marginLeft: 'auto',
                        marginRight: 'auto',
                      }}
                    >
                      <circle cx="11" cy="11" r="8" />
                      <line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    尚無相似歷史案例記錄
                  </div>
                ) : (
                  similarCases.map((c) => {
                    const pct = c.similarity
                    const pctStyle =
                      pct >= 85
                        ? { background: '#fef2f2', color: '#b91c1c', border: '1px solid #fecaca' }
                        : pct >= 70
                          ? { background: '#fff7ed', color: '#b45309', border: '1px solid #fed7aa' }
                          : { background: '#f8fafc', color: '#475569', border: '1px solid #cbd5e1' }
                    const outcomeStyle = OUTCOME_STYLE[c.outcome] || OUTCOME_STYLE['已緩解']
                    return (
                      <div
                        key={c.id}
                        style={{
                          border: '1px solid #e2e8f0',
                          borderRadius: 8,
                          padding: '12px 14px',
                          marginBottom: 12,
                          background: 'white',
                        }}
                      >
                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            justifyContent: 'space-between',
                            gap: 10,
                            marginBottom: 8,
                          }}
                        >
                          <div>
                            <div
                              style={{
                                fontSize: 13,
                                fontWeight: 700,
                                color: '#1e293b',
                                marginBottom: 3,
                              }}
                            >
                              {c.title}
                            </div>
                            <div style={{ fontSize: 11, color: '#94a3b8' }}>{c.date}</div>
                          </div>
                          <span
                            style={{
                              fontSize: 11,
                              fontWeight: 700,
                              padding: '2px 7px',
                              borderRadius: 4,
                              flexShrink: 0,
                              ...pctStyle,
                            }}
                          >
                            相似度 {pct}%
                          </span>
                        </div>
                        <div
                          style={{
                            fontSize: 13,
                            color: '#475569',
                            lineHeight: 1.6,
                            marginBottom: 8,
                          }}
                        >
                          {c.summary}
                        </div>
                        <div
                          style={{
                            background: '#f8fafc',
                            borderRadius: 6,
                            padding: '8px 10px',
                            border: '1px solid #f1f5f9',
                          }}
                        >
                          <div
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              marginBottom: 4,
                            }}
                          >
                            <span style={{ fontSize: 11, fontWeight: 700, color: '#64748b' }}>
                              最終處置方式
                            </span>
                            {c.resolvedAt && (
                              <span style={{ fontSize: 10, color: '#94a3b8' }}>
                                🕐 {c.resolvedAt}
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: 12, color: '#334155', lineHeight: 1.5 }}>
                            {c.resolution}
                          </div>
                          {c.resolvedBy && (
                            <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
                              處理人：{c.resolvedBy}
                            </div>
                          )}
                        </div>
                        <div style={{ marginTop: 8 }}>
                          <span
                            style={{
                              display: 'inline-block',
                              fontSize: 11,
                              fontWeight: 700,
                              padding: '2px 7px',
                              borderRadius: 4,
                              ...outcomeStyle,
                            }}
                          >
                            {c.outcome}
                          </span>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            )}

            {/* Tab 3: 處置紀錄 */}
            {activeTab === 'diary' && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#94a3b8"
                    strokeWidth="2"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  <span style={{ fontSize: 14, fontWeight: 700, color: '#1e293b' }}>處置紀錄</span>
                  <span style={{ fontSize: 11, color: '#94a3b8' }}>— 記錄每次處理動作與備註</span>
                </div>

                {/* History list */}
                <div style={{ marginBottom: 14 }}>
                  {!issue.history || issue.history.length === 0 ? (
                    <div style={{ fontSize: 13, color: '#94a3b8', padding: '4px 0' }}>
                      （尚無處置紀錄）
                    </div>
                  ) : (
                    issue.history.map((h, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          gap: 10,
                          alignItems: 'flex-start',
                          padding: '6px 0',
                          borderBottom: '1px solid #f1f5f9',
                        }}
                      >
                        <span
                          style={{
                            fontSize: 11,
                            color: '#94a3b8',
                            whiteSpace: 'nowrap',
                            minWidth: 110,
                            paddingTop: 1,
                          }}
                        >
                          {h.date}
                        </span>
                        <span
                          style={{
                            fontSize: 12,
                            fontWeight: 600,
                            color: '#2e3f6e',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {h.user}
                        </span>
                        <span style={{ fontSize: 13, color: '#334155', flex: 1 }}>
                          {h.note}
                          {h.statusChange && (
                            <span
                              style={{
                                fontSize: 11,
                                fontWeight: 600,
                                padding: '1px 6px',
                                borderRadius: 3,
                                marginLeft: 6,
                                ...(OUTCOME_STYLE[h.statusChange] || {
                                  background: '#f8fafc',
                                  color: '#475569',
                                  border: '1px solid #cbd5e1',
                                }),
                              }}
                            >
                              {h.statusChange}
                            </span>
                          )}
                        </span>
                        <span
                          onClick={() => deleteHistoryEntry(idx)}
                          title="刪除"
                          style={{
                            cursor: 'pointer',
                            flexShrink: 0,
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: 22,
                            height: 22,
                            borderRadius: 4,
                            color: '#94a3b8',
                            transition: 'all 0.15s',
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.color = '#ef4444'
                            e.currentTarget.style.background = '#fef2f2'
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.color = '#94a3b8'
                            e.currentTarget.style.background = 'transparent'
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
                            <line x1="18" y1="6" x2="6" y2="18" />
                            <line x1="6" y1="6" x2="18" y2="18" />
                          </svg>
                        </span>
                      </div>
                    ))
                  )}
                </div>

                {/* Resolution block (shown when status = 已完成) */}
                {showResolution && (
                  <div
                    style={{
                      display: 'block',
                      marginTop: 12,
                      padding: '12px 14px',
                      background: '#f0fdf4',
                      border: '1.5px solid #86efac',
                      borderRadius: 8,
                      marginBottom: 14,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 12,
                        fontWeight: 700,
                        color: '#166534',
                        marginBottom: 6,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                      }}
                    >
                      <svg
                        width="13"
                        height="13"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#166534"
                        strokeWidth="2.5"
                      >
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                        <polyline points="22 4 12 14.01 9 11.01" />
                      </svg>
                      結案說明（必填）
                    </div>
                    <div style={{ fontSize: 11, color: '#4d7c60', marginBottom: 8 }}>
                      狀態已設為「已完成」，請填寫最終處置方式，這將作為日後相似案例的參考依據。
                    </div>
                    <div style={{ display: 'flex', gap: 10, marginBottom: 8 }}>
                      <div style={{ flex: 1 }}>
                        <label
                          style={{
                            fontSize: 11,
                            color: '#166534',
                            fontWeight: 700,
                            display: 'block',
                            marginBottom: 3,
                          }}
                        >
                          處理人
                        </label>
                        <input
                          type="text"
                          value={resHandler}
                          onChange={(e) => setResHandler(e.target.value)}
                          placeholder="處理人姓名"
                          style={{
                            width: '100%',
                            boxSizing: 'border-box',
                            height: 32,
                            padding: '0 8px',
                            border: '1.5px solid #86efac',
                            borderRadius: 6,
                            fontSize: 13,
                            outline: 'none',
                            background: 'white',
                            color: '#1e293b',
                          }}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <label
                          style={{
                            fontSize: 11,
                            color: '#166534',
                            fontWeight: 700,
                            display: 'block',
                            marginBottom: 3,
                          }}
                        >
                          處置時間
                        </label>
                        <input
                          type="datetime-local"
                          value={resTime}
                          onChange={(e) => setResTime(e.target.value)}
                          style={{
                            width: '100%',
                            boxSizing: 'border-box',
                            height: 32,
                            padding: '0 8px',
                            border: '1.5px solid #86efac',
                            borderRadius: 6,
                            fontSize: 13,
                            outline: 'none',
                            background: 'white',
                            color: '#1e293b',
                          }}
                        />
                      </div>
                    </div>
                    <textarea
                      value={resText}
                      onChange={(e) => setResText(e.target.value)}
                      rows={3}
                      placeholder="例如：已隔離主機並重新安裝 OS，更新防火牆 GeoIP 規則封鎖惡意 IP，部署 NDR 監控..."
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        padding: '8px 10px',
                        border: '1.5px solid #86efac',
                        borderRadius: 6,
                        fontFamily: 'inherit',
                        fontSize: 13,
                        outline: 'none',
                        resize: 'vertical',
                        background: 'white',
                        color: '#1e293b',
                      }}
                    />
                    <button
                      onClick={saveResolution}
                      style={{
                        marginTop: 8,
                        background: '#166534',
                        color: 'white',
                        border: 'none',
                        borderRadius: 6,
                        fontSize: 12,
                        padding: '6px 14px',
                        cursor: 'pointer',
                        fontWeight: 700,
                      }}
                    >
                      儲存結案說明
                    </button>
                  </div>
                )}

                {/* Add history entry form */}
                <div
                  style={{
                    display: 'flex',
                    gap: 8,
                    flexWrap: 'nowrap',
                    alignItems: 'flex-end',
                    padding: 12,
                    background: '#f8fafc',
                    borderRadius: 8,
                    border: '1px solid #e2e8f0',
                  }}
                >
                  <div>
                    <label
                      style={{ fontSize: 11, color: '#64748b', display: 'block', marginBottom: 3 }}
                    >
                      日期
                    </label>
                    <input
                      type="datetime-local"
                      value={histDate}
                      onChange={(e) => setHistDate(e.target.value)}
                      style={{
                        height: 36,
                        padding: '0 8px',
                        border: '1px solid #cbd5e1',
                        borderRadius: 6,
                        fontSize: 13,
                        outline: 'none',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                  <div style={{ flex: 1 }}>
                    <label
                      style={{ fontSize: 11, color: '#64748b', display: 'block', marginBottom: 3 }}
                    >
                      備註
                    </label>
                    <input
                      type="text"
                      value={histNote}
                      onChange={(e) => setHistNote(e.target.value)}
                      placeholder="輸入處理動作備註..."
                      style={{
                        height: 36,
                        width: '100%',
                        padding: '0 8px',
                        border: '1px solid #cbd5e1',
                        borderRadius: 6,
                        fontSize: 13,
                        outline: 'none',
                        boxSizing: 'border-box',
                      }}
                    />
                  </div>
                  <div>
                    <label
                      style={{ fontSize: 11, color: '#64748b', display: 'block', marginBottom: 3 }}
                    >
                      變更狀態
                    </label>
                    <select
                      value={histStatus}
                      onChange={(e) => setHistStatus(e.target.value)}
                      style={{
                        height: 36,
                        padding: '0 8px',
                        border: '1px solid #cbd5e1',
                        borderRadius: 6,
                        fontSize: 13,
                        outline: 'none',
                        boxSizing: 'border-box',
                        minWidth: 100,
                      }}
                    >
                      {['未處理', '處理中', '已完成', '擱置'].map((s) => (
                        <option key={s}>{s}</option>
                      ))}
                    </select>
                  </div>
                  <button
                    onClick={addHistoryEntry}
                    style={{
                      height: 36,
                      padding: '0 14px',
                      background: '#2e3f6e',
                      color: 'white',
                      border: 'none',
                      borderRadius: 6,
                      fontSize: 13,
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    新增
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right: Chat Panel */}
        <div
          style={{
            width: chatVisible ? 360 : 40,
            flexShrink: 0,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
            overflow: 'hidden',
            transition: 'width 0.2s',
          }}
        >
          {/* Chat header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 8,
              flexShrink: 0,
            }}
          >
            {chatVisible && (
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  color: '#1e293b',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#2e3f6e"
                  strokeWidth="2"
                >
                  <rect x="4" y="8" width="16" height="12" rx="2" />
                  <path d="M9 13h0M15 13h0" strokeWidth="3" strokeLinecap="round" />
                  <path d="M12 2v4M2 12h2M20 12h2" />
                </svg>
                諮詢資安專家
              </div>
            )}
            <button
              onClick={() => setChatVisible((v) => !v)}
              title={chatVisible ? '收合' : '展開'}
              style={{
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 28,
                height: 28,
                borderRadius: 6,
                border: '1.5px solid #cbd5e1',
                background: 'white',
                flexShrink: 0,
                marginLeft: chatVisible ? 0 : 'auto',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#eef1f8'
                e.currentTarget.style.borderColor = '#2e3f6e'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'white'
                e.currentTarget.style.borderColor = '#cbd5e1'
              }}
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#2e3f6e"
                strokeWidth="2.5"
              >
                {chatVisible ? (
                  <polyline points="15 18 9 12 15 6" />
                ) : (
                  <polyline points="9 18 15 12 9 6" />
                )}
              </svg>
            </button>
          </div>

          {chatVisible && (
            <div
              style={{
                background: 'white',
                borderRadius: 12,
                display: 'flex',
                flexDirection: 'column',
                border: '1px solid #e2e8f0',
                minHeight: 0,
                overflow: 'hidden',
                flex: 1,
              }}
            >
              {/* Messages */}
              <div
                style={{
                  flex: 1,
                  padding: 15,
                  overflowY: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10,
                  minHeight: 0,
                }}
              >
                {chatMsgs.map((m, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '10px 14px',
                      borderRadius: 10,
                      maxWidth: '85%',
                      lineHeight: 1.5,
                      fontSize: 14,
                      whiteSpace: 'pre-wrap',
                      ...(m.role === 'user'
                        ? { background: '#2e3f6e', color: 'white', alignSelf: 'flex-end' }
                        : m.role === 'typing'
                          ? {
                              background: '#f1f5f9',
                              color: '#94a3b8',
                              alignSelf: 'flex-start',
                              border: '1px solid #e2e8f0',
                              fontStyle: 'italic',
                            }
                          : {
                              background: '#f1f5f9',
                              alignSelf: 'flex-start',
                              border: '1px solid #e2e8f0',
                            }),
                    }}
                  >
                    {m.role === 'typing' ? '資安專家分析中…' : m.content}
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Quick chips */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 5,
                  padding: '8px 10px',
                  borderTop: '1px solid #e2e8f0',
                  background: '#f8fafc',
                }}
              >
                {['整體摘要', '相關發現', '補充說明', '修復建議'].map((type) => (
                  <button
                    key={type}
                    onClick={() => sendQuickChat(type)}
                    style={{
                      padding: '7px 10px',
                      borderRadius: 7,
                      border: '1.5px solid #c5ccdf',
                      background: 'white',
                      color: '#2e3f6e',
                      fontSize: 12,
                      fontWeight: 700,
                      cursor: 'pointer',
                      transition: 'all 0.15s',
                      whiteSpace: 'nowrap',
                      textAlign: 'left',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 5,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = '#eef1f8'
                      e.currentTarget.style.borderColor = '#2e3f6e'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'white'
                      e.currentTarget.style.borderColor = '#c5ccdf'
                    }}
                  >
                    {type}
                  </button>
                ))}
              </div>

              {/* Input */}
              <div
                style={{
                  padding: 12,
                  borderTop: '1px solid #e2e8f0',
                  display: 'flex',
                  gap: 8,
                  alignItems: 'center',
                  background: '#f8fafc',
                  borderRadius: '0 0 12px 12px',
                }}
              >
                <input
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendMsg()}
                  placeholder="請針對此事件提出疑問..."
                  style={{
                    flex: 1,
                    padding: '10px 16px',
                    border: '1px solid #cbd5e1',
                    borderRadius: 20,
                    outline: 'none',
                    fontFamily: 'inherit',
                    fontSize: 13,
                  }}
                />
                <button
                  onClick={() => sendMsg()}
                  style={{
                    background: '#2e3f6e',
                    color: 'white',
                    border: 'none',
                    width: 38,
                    height: 38,
                    borderRadius: '50%',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <line x1="22" y1="2" x2="11" y2="13" />
                    <polygon points="22 2 15 22 11 13 2 9 22 2" />
                  </svg>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
