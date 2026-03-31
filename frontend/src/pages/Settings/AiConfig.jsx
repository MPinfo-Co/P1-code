import { useState } from 'react'
import { aiPartners as initialPartners } from '../../data/aiPartners'
import Badge from '../../components/ui/Badge'

const MODEL_OPTIONS = ['Gemini 1.5 Pro', 'Gemini 1.5 Flash', 'OpenAI GPT-4o', 'Claude 3.5 Sonnet']

const MOCK_KB_LIST = [
  { id: 'kb1', name: '資安事件知識庫', desc: '資安威脅、漏洞、處置方法' },
  { id: 'kb2', name: '防火牆規則庫', desc: 'Fortinet / Cisco 設定指引' },
  { id: 'kb3', name: '安全 IP 白名單', desc: '受信任的 IP 位址清單' },
]

// Builtin config form
// eslint-disable-next-line no-unused-vars
function BuiltinConfigForm({ partner, onBack }) {
  const [notifyLevel, setNotifyLevel] = useState('4 星以上即通知')
  const [reportStyle, setReportStyle] = useState('技術詳細版（給資安工程師）')
  const [notifyOnChange, setNotifyOnChange] = useState(false)
  const [notifyOnLog, setNotifyOnLog] = useState(true)
  const [notifyEmail, setNotifyEmail] = useState('')
  const [boundKbs, setBoundKbs] = useState(['kb1'])

  function toggleKb(id) {
    setBoundKbs((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 20,
        }}
      >
        <p style={{ fontSize: 13, color: '#64748b' }}>
          可設定項目：核心推理模型、綁定知識庫、通知觸發條件與通知準則。
        </p>
        <button
          onClick={onBack}
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
          onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
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

      <div className="bg-white rounded-xl border border-slate-200">
        {/* 核心推理模型 */}
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0' }}>
          <h3
            style={{
              marginBottom: 12,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 15,
              fontWeight: 700,
            }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#2e3f6e"
              strokeWidth="2"
            >
              <polygon points="12 2 2 7 12 12 22 7 12 2" />
              <polyline points="2 17 12 22 22 17" />
              <polyline points="2 12 12 17 22 12" />
            </svg>
            核心推理模型
          </h3>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '12px 16px',
              background: '#f1f5f9',
              borderRadius: 8,
              border: '1px solid #e2e8f0',
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#2e3f6e"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <div>
              <div style={{ fontWeight: 700, color: '#1e293b', fontSize: 14 }}>Gemini 1.5 Pro</div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
                由系統預設配置，已針對資安分析情境調優，無需調整。
              </div>
            </div>
          </div>
        </div>

        {/* 綁定知識庫 */}
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0' }}>
          <h3
            style={{
              marginBottom: 10,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 15,
              fontWeight: 700,
              flexWrap: 'wrap',
            }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#64748b"
              strokeWidth="2"
            >
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
            綁定知識庫
            <span style={{ fontSize: 11, color: '#94a3b8', fontWeight: 400 }}>
              (勾選此 AI 夥伴可引用的知識庫，支援多選)
            </span>
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {MOCK_KB_LIST.map((kb) => (
              <label
                key={kb.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 14px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 8,
                  cursor: 'pointer',
                  background: boundKbs.includes(kb.id) ? '#eef1f8' : 'white',
                }}
              >
                <input
                  type="checkbox"
                  checked={boundKbs.includes(kb.id)}
                  onChange={() => toggleKb(kb.id)}
                  style={{ width: 15, height: 15, accentColor: '#2e3f6e' }}
                />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{kb.name}</div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>{kb.desc}</div>
                </div>
              </label>
            ))}
          </div>
          <div style={{ marginTop: 10 }}>
            <span style={{ fontSize: 12, color: '#2e3f6e', fontWeight: 600 }}>
              前往管理知識庫 →
            </span>
          </div>
        </div>

        {/* 通知設定 */}
        <div style={{ padding: '20px 24px' }}>
          <h3
            style={{
              marginBottom: 16,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 15,
              fontWeight: 700,
            }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#7c3aed"
              strokeWidth="2"
            >
              <path d="M22 17H2a3 3 0 0 0 3-3V9a7 7 0 0 1 14 0v5a3 3 0 0 0 3 3zm-8.27 4a2 2 0 0 1-3.46 0" />
            </svg>
            通知設定
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>
                通知觸發條件
              </label>
              <select
                value={notifyLevel}
                onChange={(e) => setNotifyLevel(e.target.value)}
                style={{
                  width: '100%',
                  marginTop: 0,
                  height: 36,
                  padding: '0 10px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 6,
                  fontSize: 13,
                  outline: 'none',
                  background: 'white',
                }}
              >
                <option>3 星以上即通知</option>
                <option>4 星以上即通知</option>
                <option>僅 5 星通知</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>
                報告語氣 / 格式
              </label>
              <select
                value={reportStyle}
                onChange={(e) => setReportStyle(e.target.value)}
                style={{
                  width: '100%',
                  height: 36,
                  padding: '0 10px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 6,
                  fontSize: 13,
                  outline: 'none',
                  background: 'white',
                }}
              >
                <option>技術詳細版（給資安工程師）</option>
                <option>摘要版（給主管 / CISO）</option>
                <option>雙版並陳</option>
              </select>
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>
                通知準則
              </label>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                  padding: '10px 14px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 8,
                  background: '#f8fafc',
                }}
              >
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    fontSize: 13,
                    color: '#334155',
                    cursor: 'default',
                  }}
                >
                  <input
                    type="checkbox"
                    checked
                    disabled
                    style={{ width: 15, height: 15, accentColor: '#2e3f6e' }}
                  />
                  <span>
                    <strong>Owner 優先通知</strong>（不可停用）— 負責人一律接收所有指派事件通知
                  </span>
                </label>
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    fontSize: 13,
                    color: '#334155',
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={notifyOnChange}
                    onChange={(e) => setNotifyOnChange(e.target.checked)}
                    style={{ width: 15, height: 15, accentColor: '#2e3f6e' }}
                  />
                  <span>事件狀態變更時通知負責人</span>
                </label>
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    fontSize: 13,
                    color: '#334155',
                    cursor: 'pointer',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={notifyOnLog}
                    onChange={(e) => setNotifyOnLog(e.target.checked)}
                    style={{ width: 15, height: 15, accentColor: '#2e3f6e' }}
                  />
                  <span>新增操作記錄時通知負責人</span>
                </label>
              </div>
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>
                Email 通知對象
              </label>
              <input
                type="text"
                value={notifyEmail}
                onChange={(e) => setNotifyEmail(e.target.value)}
                placeholder="soc-team@company.com"
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  height: 36,
                  padding: '0 10px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 6,
                  fontSize: 13,
                  outline: 'none',
                }}
              />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ fontSize: 13, fontWeight: 600, display: 'block', marginBottom: 6 }}>
                安全 IP 名單
              </label>
              <div
                style={{
                  padding: '12px 14px',
                  background: '#f8fafc',
                  borderRadius: 8,
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <span style={{ fontSize: 13, color: '#64748b' }}>
                  安全 IP 名單已整合至知識庫統一管理，請前往知識庫的「安全 IP
                  白名單」資料表進行維護。
                </span>
                <span
                  style={{
                    fontSize: 12,
                    color: '#2e3f6e',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    marginLeft: 12,
                  }}
                >
                  前往知識庫 →
                </span>
              </div>
            </div>
          </div>
        </div>

        <div style={{ padding: '16px 24px', borderTop: '1px solid #e2e8f0', textAlign: 'right' }}>
          <button
            onClick={() => {
              alert('夥伴設定已儲存')
              onBack()
            }}
            className="px-5 py-2.5 bg-[#2e3f6e] text-white rounded-lg text-sm font-bold hover:bg-[#1e2d52] transition-colors"
          >
            儲存設定
          </button>
        </div>
      </div>
    </div>
  )
}

// Custom config form
// eslint-disable-next-line no-unused-vars
function CustomConfigForm({ partner, onBack }) {
  const [model, setModel] = useState('Gemini 1.5 Flash')
  const [prompt, setPrompt] = useState('')
  const [boundKbs, setBoundKbs] = useState([])

  function toggleKb(id) {
    setBoundKbs((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 20,
        }}
      >
        <p style={{ fontSize: 13, color: '#64748b' }}>
          自訂此 AI 夥伴的推理模型、角色定義與綁定知識庫。
        </p>
        <button
          onClick={onBack}
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
          onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
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

      <div className="bg-white rounded-xl border border-slate-200">
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0' }}>
          <h3
            style={{
              marginBottom: 12,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 15,
              fontWeight: 700,
            }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#2e3f6e"
              strokeWidth="2"
            >
              <polygon points="12 2 2 7 12 12 22 7 12 2" />
              <polyline points="2 17 12 22 22 17" />
              <polyline points="2 12 12 17 22 12" />
            </svg>
            核心模型選擇
          </h3>
          <label style={{ fontSize: 13, color: '#64748b', display: 'block', marginBottom: 6 }}>
            決定此 AI 夥伴的底層推理模型
          </label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            style={{
              width: '100%',
              height: 38,
              padding: '0 10px',
              border: '1px solid #e2e8f0',
              borderRadius: 6,
              fontSize: 13,
              outline: 'none',
              background: 'white',
            }}
          >
            {MODEL_OPTIONS.map((m) => (
              <option key={m}>{m}</option>
            ))}
          </select>
        </div>

        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0' }}>
          <h3
            style={{
              marginBottom: 12,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 15,
              fontWeight: 700,
            }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#ea580c"
              strokeWidth="2"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
            系統提示詞 (System Prompt)
          </h3>
          <label style={{ fontSize: 13, color: '#64748b', display: 'block', marginBottom: 6 }}>
            請依照「角色 + 任務 + 限制」格式定義此 AI 夥伴：
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={6}
            placeholder="例如：你是一位專精於電商訂單流程的助理，負責自動分類客戶退換貨請求，並依照【退換貨 SOP】回覆標準處置方式..."
            style={{
              width: '100%',
              boxSizing: 'border-box',
              padding: '10px 12px',
              border: '1px solid #e2e8f0',
              borderRadius: 6,
              fontFamily: 'inherit',
              fontSize: 13,
              outline: 'none',
              resize: 'vertical',
            }}
          />
        </div>

        <div style={{ padding: '20px 24px' }}>
          <h3
            style={{
              marginBottom: 10,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 15,
              fontWeight: 700,
              flexWrap: 'wrap',
            }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#64748b"
              strokeWidth="2"
            >
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
            綁定知識庫
            <span style={{ fontSize: 11, color: '#94a3b8', fontWeight: 400 }}>
              (勾選此 AI 夥伴可引用的知識庫)
            </span>
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {MOCK_KB_LIST.map((kb) => (
              <label
                key={kb.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 14px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 8,
                  cursor: 'pointer',
                  background: boundKbs.includes(kb.id) ? '#eef1f8' : 'white',
                }}
              >
                <input
                  type="checkbox"
                  checked={boundKbs.includes(kb.id)}
                  onChange={() => toggleKb(kb.id)}
                  style={{ width: 15, height: 15, accentColor: '#2e3f6e' }}
                />
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{kb.name}</div>
                  <div style={{ fontSize: 12, color: '#64748b' }}>{kb.desc}</div>
                </div>
              </label>
            ))}
          </div>
          <div style={{ marginTop: 10 }}>
            <span style={{ fontSize: 12, color: '#2e3f6e', fontWeight: 600 }}>
              前往管理知識庫 →
            </span>
          </div>
        </div>

        <div style={{ padding: '16px 24px', borderTop: '1px solid #e2e8f0', textAlign: 'right' }}>
          <button
            onClick={() => {
              alert('夥伴設定已儲存')
              onBack()
            }}
            className="px-5 py-2.5 bg-[#2e3f6e] text-white rounded-lg text-sm font-bold hover:bg-[#1e2d52] transition-colors"
          >
            儲存設定
          </button>
        </div>
      </div>
    </div>
  )
}

// Add partner form
function AddPartnerForm({ onBack }) {
  const [name, setName] = useState('')
  const [model, setModel] = useState('Gemini 1.5 Flash')
  const [prompt, setPrompt] = useState('')

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 20,
        }}
      >
        <p style={{ fontSize: 13, color: '#64748b' }}>設定新 AI 夥伴的名稱、推理模型與角色定義。</p>
        <button
          onClick={onBack}
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
          onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
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

      <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-5">
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">夥伴名稱</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例如：法務遵循專家"
            className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm outline-none focus:border-indigo-400"
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1.5">核心模型</label>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm outline-none"
          >
            {MODEL_OPTIONS.map((m) => (
              <option key={m}>{m}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">
            系統提示詞 (System Prompt)
          </label>
          <p className="text-xs text-slate-500 mb-2">定義 AI 夥伴的角色性格與專業範圍。</p>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={5}
            placeholder="例如：你是一位專精於台灣勞動基準法的法律顧問..."
            className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm outline-none resize-y"
          />
        </div>
        <div className="text-right">
          <button
            onClick={() => {
              alert('夥伴已建立')
              onBack()
            }}
            className="px-5 py-2.5 bg-[#2e3f6e] text-white rounded-lg text-sm font-bold hover:bg-[#1e2d52] transition-colors"
          >
            確認新增
          </button>
        </div>
      </div>
    </div>
  )
}

// Main component
export default function AiConfig() {
  const [partners] = useState(initialPartners)
  const [view, setView] = useState('list') // 'list' | 'builtin' | 'custom' | 'add'
  const [selectedPartner, setSelectedPartner] = useState(null)

  function openConfig(partner) {
    setSelectedPartner(partner)
    setView(partner.builtin ? 'builtin' : 'custom')
  }

  if (view === 'builtin' && selectedPartner) {
    return <BuiltinConfigForm partner={selectedPartner} onBack={() => setView('list')} />
  }
  if (view === 'custom' && selectedPartner) {
    return <CustomConfigForm partner={selectedPartner} onBack={() => setView('list')} />
  }
  if (view === 'add') {
    return <AddPartnerForm onBack={() => setView('list')} />
  }

  return (
    <div>
      <div className="flex justify-end items-center mb-4">
        <button
          onClick={() => setView('add')}
          className="flex items-center gap-1.5 px-4 py-2 bg-[#2e3f6e] text-white rounded-lg text-sm font-bold hover:bg-[#1e2d52] transition-colors"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          新增AI夥伴
        </button>
      </div>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              {['AI夥伴名稱', '狀態', '說明', '執行動作'].map((h) => (
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
            {partners.map((p) => (
              <tr
                key={p.id}
                className={`border-b border-slate-100 ${p.disabled ? 'opacity-60 bg-slate-50' : ''}`}
              >
                <td className="px-4 py-3.5 text-sm font-semibold text-slate-700">
                  {p.name}
                  <Badge variant={p.builtin ? 'builtin' : 'new'}>
                    {p.builtin ? '預設' : '自訂'}
                  </Badge>
                </td>
                <td className="px-4 py-3.5 text-sm">
                  <span
                    className={`font-bold ${p.disabled ? 'text-slate-400' : 'text-emerald-600'}`}
                  >
                    {p.disabled ? '○ 停用中' : '● 啟用中'}
                  </span>
                </td>
                <td className="px-4 py-3.5 text-sm text-slate-500">{p.description ?? '—'}</td>
                <td className="px-4 py-3.5">
                  <div className="flex gap-2">
                    <button
                      onClick={() => openConfig(p)}
                      className="text-sm font-semibold text-slate-500 border border-slate-300 px-3 py-1 rounded-md hover:bg-slate-50"
                    >
                      夥伴設定
                    </button>
                    {!p.builtin && (
                      <button className="text-sm font-semibold text-red-500 border border-red-200 px-3 py-1 rounded-md hover:bg-red-50">
                        刪除
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
