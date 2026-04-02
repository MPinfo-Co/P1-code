import { useState } from 'react'
import { aiPartners as initialPartners } from '../../data/aiPartners'
import {
  Box,
  Button,
  Chip,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  FormLabel,
  Checkbox,
  FormControlLabel,
} from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'

const MODEL_OPTIONS = ['Gemini 1.5 Pro', 'Gemini 1.5 Flash', 'OpenAI GPT-4o', 'Claude 3.5 Sonnet']

const MOCK_KB_LIST = [
  { id: 'kb1', name: '資安事件知識庫', desc: '資安威脅、漏洞、處置方法' },
  { id: 'kb2', name: '防火牆規則庫', desc: 'Fortinet / Cisco 設定指引' },
  { id: 'kb3', name: '安全 IP 白名單', desc: '受信任的 IP 位址清單' },
]

// Builtin config form
function BuiltinConfigForm({ onBack }) {
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
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2.5 }}>
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>
          可設定項目：核心推理模型、綁定知識庫、通知觸發條件與通知準則。
        </Typography>
        <Button
          variant="outlined"
          startIcon={
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
          }
          onClick={onBack}
          sx={{
            fontSize: 13.5,
            fontWeight: 600,
            borderColor: '#cbd5e1',
            color: '#334155',
            '&:hover': { background: '#f8fafc', borderColor: '#cbd5e1' },
          }}
        >
          回上一頁
        </Button>
      </Box>

      <Box sx={{ bgcolor: 'white', borderRadius: 2, border: '1px solid #e2e8f0' }}>
        {/* 核心推理模型 */}
        <Box sx={{ p: '20px 24px', borderBottom: '1px solid #e2e8f0' }}>
          <Typography
            sx={{
              mb: 1.5,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
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
          </Typography>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1.5,
              p: '12px 16px',
              background: '#f1f5f9',
              borderRadius: 2,
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
            <Box>
              <Typography sx={{ fontWeight: 700, color: '#1e293b', fontSize: 14 }}>
                Gemini 1.5 Pro
              </Typography>
              <Typography sx={{ fontSize: 12, color: '#64748b', mt: 0.25 }}>
                由系統預設配置，已針對資安分析情境調優，無需調整。
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* 綁定知識庫 */}
        <Box sx={{ p: '20px 24px', borderBottom: '1px solid #e2e8f0' }}>
          <Typography
            sx={{
              mb: 1.25,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
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
            <Typography component="span" sx={{ fontSize: 11, color: '#94a3b8', fontWeight: 400 }}>
              (勾選此 AI 夥伴可引用的知識庫，支援多選)
            </Typography>
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {MOCK_KB_LIST.map((kb) => (
              <Box
                key={kb.id}
                component="label"
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.25,
                  p: '10px 14px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 2,
                  cursor: 'pointer',
                  background: boundKbs.includes(kb.id) ? '#eef1f8' : 'white',
                }}
              >
                <Checkbox
                  checked={boundKbs.includes(kb.id)}
                  onChange={() => toggleKb(kb.id)}
                  size="small"
                  sx={{ p: 0, color: '#2e3f6e', '&.Mui-checked': { color: '#2e3f6e' } }}
                />
                <Box>
                  <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                    {kb.name}
                  </Typography>
                  <Typography sx={{ fontSize: 12, color: '#64748b' }}>{kb.desc}</Typography>
                </Box>
              </Box>
            ))}
          </Box>
          <Box sx={{ mt: 1.25 }}>
            <Typography
              component="span"
              sx={{ fontSize: 12, color: '#2e3f6e', fontWeight: 600, cursor: 'pointer' }}
            >
              前往管理知識庫 →
            </Typography>
          </Box>
        </Box>

        {/* 通知設定 */}
        <Box sx={{ p: '20px 24px' }}>
          <Typography
            sx={{
              mb: 2,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
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
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <FormControl size="small">
              <FormLabel sx={{ fontSize: 13, fontWeight: 600, color: '#334155', mb: 0.75 }}>
                通知觸發條件
              </FormLabel>
              <Select
                value={notifyLevel}
                onChange={(e) => setNotifyLevel(e.target.value)}
                sx={{ fontSize: 13 }}
              >
                <MenuItem value="3 星以上即通知" sx={{ fontSize: 13 }}>
                  3 星以上即通知
                </MenuItem>
                <MenuItem value="4 星以上即通知" sx={{ fontSize: 13 }}>
                  4 星以上即通知
                </MenuItem>
                <MenuItem value="僅 5 星通知" sx={{ fontSize: 13 }}>
                  僅 5 星通知
                </MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small">
              <FormLabel sx={{ fontSize: 13, fontWeight: 600, color: '#334155', mb: 0.75 }}>
                報告語氣 / 格式
              </FormLabel>
              <Select
                value={reportStyle}
                onChange={(e) => setReportStyle(e.target.value)}
                sx={{ fontSize: 13 }}
              >
                <MenuItem value="技術詳細版（給資安工程師）" sx={{ fontSize: 13 }}>
                  技術詳細版（給資安工程師）
                </MenuItem>
                <MenuItem value="摘要版（給主管 / CISO）" sx={{ fontSize: 13 }}>
                  摘要版（給主管 / CISO）
                </MenuItem>
                <MenuItem value="雙版並陳" sx={{ fontSize: 13 }}>
                  雙版並陳
                </MenuItem>
              </Select>
            </FormControl>
            <Box sx={{ gridColumn: '1 / -1' }}>
              <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#334155', mb: 0.75 }}>
                通知準則
              </Typography>
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 0.75,
                  p: '10px 14px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 2,
                  background: '#f8fafc',
                }}
              >
                <FormControlLabel
                  control={
                    <Checkbox
                      checked
                      disabled
                      size="small"
                      sx={{ py: 0, color: '#2e3f6e', '&.Mui-checked': { color: '#2e3f6e' } }}
                    />
                  }
                  label={
                    <Typography sx={{ fontSize: 13, color: '#334155' }}>
                      <strong>Owner 優先通知</strong>（不可停用）— 負責人一律接收所有指派事件通知
                    </Typography>
                  }
                  sx={{ m: 0 }}
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={notifyOnChange}
                      onChange={(e) => setNotifyOnChange(e.target.checked)}
                      size="small"
                      sx={{ py: 0, color: '#2e3f6e', '&.Mui-checked': { color: '#2e3f6e' } }}
                    />
                  }
                  label={
                    <Typography sx={{ fontSize: 13, color: '#334155' }}>
                      事件狀態變更時通知負責人
                    </Typography>
                  }
                  sx={{ m: 0 }}
                />
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={notifyOnLog}
                      onChange={(e) => setNotifyOnLog(e.target.checked)}
                      size="small"
                      sx={{ py: 0, color: '#2e3f6e', '&.Mui-checked': { color: '#2e3f6e' } }}
                    />
                  }
                  label={
                    <Typography sx={{ fontSize: 13, color: '#334155' }}>
                      新增操作記錄時通知負責人
                    </Typography>
                  }
                  sx={{ m: 0 }}
                />
              </Box>
            </Box>
            <Box sx={{ gridColumn: '1 / -1' }}>
              <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#334155', mb: 0.75 }}>
                Email 通知對象
              </Typography>
              <TextField
                size="small"
                fullWidth
                value={notifyEmail}
                onChange={(e) => setNotifyEmail(e.target.value)}
                placeholder="soc-team@company.com"
                sx={{ '& .MuiInputBase-input': { fontSize: 13 } }}
              />
            </Box>
            <Box sx={{ gridColumn: '1 / -1' }}>
              <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#334155', mb: 0.75 }}>
                安全 IP 名單
              </Typography>
              <Box
                sx={{
                  p: '12px 14px',
                  background: '#f8fafc',
                  borderRadius: 2,
                  border: '1px solid #e2e8f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <Typography sx={{ fontSize: 13, color: '#64748b' }}>
                  安全 IP 名單已整合至知識庫統一管理，請前往知識庫的「安全 IP
                  白名單」資料表進行維護。
                </Typography>
                <Typography
                  sx={{
                    fontSize: 12,
                    color: '#2e3f6e',
                    fontWeight: 600,
                    whiteSpace: 'nowrap',
                    ml: 1.5,
                    cursor: 'pointer',
                  }}
                >
                  前往知識庫 →
                </Typography>
              </Box>
            </Box>
          </Box>
        </Box>

        <Box sx={{ p: '16px 24px', borderTop: '1px solid #e2e8f0', textAlign: 'right' }}>
          <Button
            variant="contained"
            onClick={() => {
              alert('夥伴設定已儲存')
              onBack()
            }}
            sx={{
              fontSize: 14,
              fontWeight: 700,
              bgcolor: '#2e3f6e',
              '&:hover': { bgcolor: '#1e2d52' },
              px: 2.5,
              py: 1.25,
            }}
          >
            儲存設定
          </Button>
        </Box>
      </Box>
    </Box>
  )
}

// Custom config form
function CustomConfigForm({ onBack }) {
  const [model, setModel] = useState('Gemini 1.5 Flash')
  const [prompt, setPrompt] = useState('')
  const [boundKbs, setBoundKbs] = useState([])

  function toggleKb(id) {
    setBoundKbs((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2.5 }}>
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>
          自訂此 AI 夥伴的推理模型、角色定義與綁定知識庫。
        </Typography>
        <Button
          variant="outlined"
          startIcon={
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
          }
          onClick={onBack}
          sx={{
            fontSize: 13.5,
            fontWeight: 600,
            borderColor: '#cbd5e1',
            color: '#334155',
            '&:hover': { background: '#f8fafc', borderColor: '#cbd5e1' },
          }}
        >
          回上一頁
        </Button>
      </Box>

      <Box sx={{ bgcolor: 'white', borderRadius: 2, border: '1px solid #e2e8f0' }}>
        <Box sx={{ p: '20px 24px', borderBottom: '1px solid #e2e8f0' }}>
          <Typography
            sx={{
              mb: 1.5,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
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
          </Typography>
          <Typography sx={{ fontSize: 13, color: '#64748b', mb: 0.75 }}>
            決定此 AI 夥伴的底層推理模型
          </Typography>
          <FormControl size="small" fullWidth>
            <Select value={model} onChange={(e) => setModel(e.target.value)} sx={{ fontSize: 13 }}>
              {MODEL_OPTIONS.map((m) => (
                <MenuItem key={m} value={m} sx={{ fontSize: 13 }}>
                  {m}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        <Box sx={{ p: '20px 24px', borderBottom: '1px solid #e2e8f0' }}>
          <Typography
            sx={{
              mb: 1.5,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
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
          </Typography>
          <Typography sx={{ fontSize: 13, color: '#64748b', mb: 0.75 }}>
            請依照「角色 + 任務 + 限制」格式定義此 AI 夥伴：
          </Typography>
          <TextField
            multiline
            rows={6}
            fullWidth
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="例如：你是一位專精於電商訂單流程的助理，負責自動分類客戶退換貨請求，並依照【退換貨 SOP】回覆標準處置方式..."
            sx={{ '& .MuiInputBase-input': { fontSize: 13 } }}
          />
        </Box>

        <Box sx={{ p: '20px 24px' }}>
          <Typography
            sx={{
              mb: 1.25,
              color: '#1e293b',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
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
            <Typography component="span" sx={{ fontSize: 11, color: '#94a3b8', fontWeight: 400 }}>
              (勾選此 AI 夥伴可引用的知識庫)
            </Typography>
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {MOCK_KB_LIST.map((kb) => (
              <Box
                key={kb.id}
                component="label"
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1.25,
                  p: '10px 14px',
                  border: '1px solid #e2e8f0',
                  borderRadius: 2,
                  cursor: 'pointer',
                  background: boundKbs.includes(kb.id) ? '#eef1f8' : 'white',
                }}
              >
                <Checkbox
                  checked={boundKbs.includes(kb.id)}
                  onChange={() => toggleKb(kb.id)}
                  size="small"
                  sx={{ p: 0, color: '#2e3f6e', '&.Mui-checked': { color: '#2e3f6e' } }}
                />
                <Box>
                  <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>
                    {kb.name}
                  </Typography>
                  <Typography sx={{ fontSize: 12, color: '#64748b' }}>{kb.desc}</Typography>
                </Box>
              </Box>
            ))}
          </Box>
          <Box sx={{ mt: 1.25 }}>
            <Typography
              component="span"
              sx={{ fontSize: 12, color: '#2e3f6e', fontWeight: 600, cursor: 'pointer' }}
            >
              前往管理知識庫 →
            </Typography>
          </Box>
        </Box>

        <Box sx={{ p: '16px 24px', borderTop: '1px solid #e2e8f0', textAlign: 'right' }}>
          <Button
            variant="contained"
            onClick={() => {
              alert('夥伴設定已儲存')
              onBack()
            }}
            sx={{
              fontSize: 14,
              fontWeight: 700,
              bgcolor: '#2e3f6e',
              '&:hover': { bgcolor: '#1e2d52' },
              px: 2.5,
              py: 1.25,
            }}
          >
            儲存設定
          </Button>
        </Box>
      </Box>
    </Box>
  )
}

// Add partner form
function AddPartnerForm({ onBack }) {
  const [name, setName] = useState('')
  const [model, setModel] = useState('Gemini 1.5 Flash')
  const [prompt, setPrompt] = useState('')

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2.5 }}>
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>
          設定新 AI 夥伴的名稱、推理模型與角色定義。
        </Typography>
        <Button
          variant="outlined"
          startIcon={
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
          }
          onClick={onBack}
          sx={{
            fontSize: 13.5,
            fontWeight: 600,
            borderColor: '#cbd5e1',
            color: '#334155',
            '&:hover': { background: '#f8fafc', borderColor: '#cbd5e1' },
          }}
        >
          回上一頁
        </Button>
      </Box>

      <Box
        sx={{
          bgcolor: 'white',
          borderRadius: 2,
          border: '1px solid #e2e8f0',
          p: 3,
          display: 'flex',
          flexDirection: 'column',
          gap: 2.5,
        }}
      >
        <Box>
          <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#334155', mb: 0.75 }}>
            夥伴名稱
          </Typography>
          <TextField
            size="small"
            fullWidth
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例如：法務遵循專家"
            sx={{ '& .MuiInputBase-input': { fontSize: 13 } }}
          />
        </Box>
        <Box>
          <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#334155', mb: 0.75 }}>
            核心模型
          </Typography>
          <FormControl size="small" fullWidth>
            <Select value={model} onChange={(e) => setModel(e.target.value)} sx={{ fontSize: 13 }}>
              {MODEL_OPTIONS.map((m) => (
                <MenuItem key={m} value={m} sx={{ fontSize: 13 }}>
                  {m}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        <Box>
          <Typography sx={{ fontSize: 13, fontWeight: 600, color: '#334155', mb: 0.5 }}>
            系統提示詞 (System Prompt)
          </Typography>
          <Typography sx={{ fontSize: 12, color: '#64748b', mb: 1 }}>
            定義 AI 夥伴的角色性格與專業範圍。
          </Typography>
          <TextField
            multiline
            rows={5}
            fullWidth
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="例如：你是一位專精於台灣勞動基準法的法律顧問..."
            sx={{ '& .MuiInputBase-input': { fontSize: 13 } }}
          />
        </Box>
        <Box sx={{ textAlign: 'right' }}>
          <Button
            variant="contained"
            onClick={() => {
              alert('夥伴已建立')
              onBack()
            }}
            sx={{
              fontSize: 14,
              fontWeight: 700,
              bgcolor: '#2e3f6e',
              '&:hover': { bgcolor: '#1e2d52' },
              px: 2.5,
              py: 1.25,
            }}
          >
            確認新增
          </Button>
        </Box>
      </Box>
    </Box>
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

  const columns = [
    {
      field: 'name',
      headerName: 'AI夥伴名稱',
      flex: 1,
      renderCell: ({ row }) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography sx={{ fontSize: 13, fontWeight: 600 }}>{row.name}</Typography>
          <Chip
            label={row.builtin ? '預設' : '自訂'}
            size="small"
            sx={{
              fontSize: 11,
              height: 20,
              bgcolor: row.builtin ? '#e8ebf5' : '#ecfdf5',
              color: row.builtin ? '#1e2d52' : '#059669',
              fontWeight: 700,
            }}
          />
        </Box>
      ),
    },
    {
      field: 'disabled',
      headerName: '狀態',
      width: 120,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, fontWeight: 700, color: value ? '#94a3b8' : '#16a34a' }}>
          {value ? '○ 停用中' : '● 啟用中'}
        </Typography>
      ),
    },
    {
      field: 'description',
      headerName: '說明',
      flex: 1.5,
      renderCell: ({ value }) => (
        <Typography sx={{ fontSize: 13, color: '#64748b' }}>{value ?? '—'}</Typography>
      ),
    },
    {
      field: 'actions',
      headerName: '執行動作',
      width: 180,
      sortable: false,
      renderCell: ({ row }) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            variant="outlined"
            sx={{ fontSize: 12, borderColor: '#cbd5e1', color: '#64748b' }}
            onClick={() => openConfig(row)}
          >
            夥伴設定
          </Button>
          {!row.builtin && (
            <Button size="small" variant="outlined" color="error" sx={{ fontSize: 12 }}>
              刪除
            </Button>
          )}
        </Box>
      ),
    },
  ]

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
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button
          variant="contained"
          startIcon={
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
          }
          onClick={() => setView('add')}
          sx={{
            fontSize: 14,
            fontWeight: 700,
            bgcolor: '#2e3f6e',
            '&:hover': { bgcolor: '#1e2d52' },
          }}
        >
          新增AI夥伴
        </Button>
      </Box>
      <Box
        sx={{ bgcolor: 'white', borderRadius: 2, border: '1px solid #e2e8f0', overflow: 'hidden' }}
      >
        <DataGrid
          rows={partners}
          columns={columns}
          autoHeight
          disableRowSelectionOnClick
          hideFooter
          sx={{
            border: 'none',
            '& .MuiDataGrid-columnHeaders': {
              bgcolor: '#f1f5f9',
              borderBottom: '2px solid #cbd5e1',
            },
            '& .MuiDataGrid-columnHeaderTitle': { fontWeight: 800, fontSize: 13, color: '#1e293b' },
            '& .MuiDataGrid-cell': {
              borderBottom: '1px solid #f1f5f9',
              display: 'flex',
              alignItems: 'center',
            },
            '& .MuiDataGrid-row:hover': { bgcolor: '#f8fafc' },
          }}
        />
      </Box>
    </Box>
  )
}
