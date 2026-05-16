// src/pages/fn_ai_partner_chat/FnAiPartnerChat.tsx
import React, { useState, useEffect, useRef, useCallback, startTransition } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import TextField from '@mui/material/TextField'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Dialog from '@mui/material/Dialog'
import DialogTitle from '@mui/material/DialogTitle'
import DialogContent from '@mui/material/DialogContent'
import DialogActions from '@mui/material/DialogActions'
import Popover from '@mui/material/Popover'
import Tooltip from '@mui/material/Tooltip'
import useMediaQuery from '@mui/material/useMediaQuery'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import SendIcon from '@mui/icons-material/Send'
import ImageIcon from '@mui/icons-material/Image'
import CloseIcon from '@mui/icons-material/Close'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import TipsAndUpdatesOutlinedIcon from '@mui/icons-material/TipsAndUpdatesOutlined'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import CheckIcon from '@mui/icons-material/Check'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'
import MicNoneIcon from '@mui/icons-material/MicNone'
import {
  useAiPartnerHistoryQuery,
  useNewAiPartnerChat,
  useSendAiPartnerMessage,
} from '@/queries/useAiPartnerChatQuery'
import type { AiPartner, ChatMessage, ChartData } from '@/queries/useAiPartnerChatQuery'

// ===== Web Speech API 型別宣告（瀏覽器原生，TypeScript 未內建）=====
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
}

interface SpeechRecognitionInstance extends EventTarget {
  lang: string
  interimResults: boolean
  continuous: boolean
  start(): void
  stop(): void
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onend: (() => void) | null
  onerror: (() => void) | null
}

interface SpeechRecognitionConstructor {
  new (): SpeechRecognitionInstance
}

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor
    webkitSpeechRecognition?: SpeechRecognitionConstructor
  }
}

interface Props {
  partner: AiPartner
  onBack: () => void
}

// ===== stripMarkdown：去除 Markdown 標記，用於複製純文字 =====
function stripMarkdown(text: string): string {
  return (
    text
      .split('\n')
      .map((line) => {
        // 程式碼區塊標記行（```...）→ 移除整行
        if (/^\s*```/.test(line)) return null
        // 表格分隔線（| --- | 或 | :--- | 等）→ 移除整行
        if (/^\|[\s\-|:]+\|$/.test(line.trim())) return null
        // 無序清單：行首 * 或 - + 空格 → 去除標記
        line = line.replace(/^(\s*)[*-]\s+/, '$1')
        // 有序清單：行首 1. 2. 等 → 去除標記
        line = line.replace(/^(\s*)\d+\.\s+/, '$1')
        // 粗體：**...**
        line = line.replace(/\*\*(.+?)\*\*/g, '$1')
        // 行內程式碼：`...`
        line = line.replace(/`([^`]*)`/g, '$1')
        // 表格列：去除首尾 | 並用空格分隔儲存格
        if (/^\|.+\|$/.test(line.trim())) {
          line = line
            .trim()
            .replace(/^\||\|$/g, '')
            .split('|')
            .map((c) => c.trim())
            .join('  ')
        }
        return line
      })
      .filter((line): line is string => line !== null)
      .join('\n')
      // 折疊連續空行為單行空行
      .replace(/\n{3,}/g, '\n\n')
      .trim()
  )
}

// ===== Markdown 渲染工具函式 =====
function escHtml(s: string): string {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function applyInline(text: string): string {
  return escHtml(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
}

function renderMarkdown(text: string): string {
  const lines = text.split('\n')
  let html = ''
  let inTable = false
  let tableHtml = ''
  let tableRowCount = 0
  let inCodeBlock = false
  let codeLines: string[] = []
  let inUl = false
  let inOl = false
  let paraLines: string[] = []

  function flushPara() {
    if (paraLines.length === 0) return
    html += `<p style="margin:0 0 6px;">${paraLines.join('<br>')}</p>`
    paraLines = []
  }

  function closeList() {
    if (inUl) {
      html += '</ul>'
      inUl = false
    }
    if (inOl) {
      html += '</ol>'
      inOl = false
    }
  }

  for (const line of lines) {
    // 程式碼區塊
    if (line.trim().startsWith('```')) {
      if (!inCodeBlock) {
        flushPara()
        closeList()
        inCodeBlock = true
        codeLines = []
      } else {
        inCodeBlock = false
        html += `<pre style="background:#1e293b;color:#e2e8f0;border-radius:6px;padding:10px 14px;font-family:monospace;font-size:12px;margin:6px 0;white-space:pre-wrap;overflow-x:auto;">${escHtml(codeLines.join('\n'))}</pre>`
        codeLines = []
      }
      continue
    }
    if (inCodeBlock) {
      codeLines.push(line)
      continue
    }

    // 表格
    const isTableRow = /^\|.+\|$/.test(line.trim())
    const isSeparator = /^\|[\s\-|:]+\|$/.test(line.trim())
    if (isTableRow && !isSeparator) {
      flushPara()
      closeList()
      if (!inTable) {
        inTable = true
        tableHtml = '<table style="border-collapse:collapse;margin:6px 0;font-size:13px;"><tbody>'
        tableRowCount = 0
      }
      const cells = line
        .trim()
        .replace(/^\||\|$/g, '')
        .split('|')
        .map((c) => c.trim())
      if (tableRowCount === 0) {
        tableHtml +=
          '<tr>' +
          cells
            .map(
              (c) =>
                `<th style="border:1px solid #c7d2fe;padding:4px 10px;text-align:left;background:#eff6ff;font-weight:600;color:#1e40af;">${applyInline(c)}</th>`
            )
            .join('') +
          '</tr>'
      } else {
        tableHtml +=
          '<tr>' +
          cells
            .map(
              (c) =>
                `<td style="border:1px solid #c7d2fe;padding:4px 10px;text-align:left;">${applyInline(c)}</td>`
            )
            .join('') +
          '</tr>'
      }
      tableRowCount++
      continue
    } else if (isSeparator) {
      continue
    } else {
      if (inTable) {
        tableHtml += '</tbody></table>'
        html += tableHtml
        inTable = false
        tableHtml = ''
        tableRowCount = 0
      }
    }

    // 無序清單
    const ulMatch = line.match(/^(\s*)[*-]\s+(.+)$/)
    if (ulMatch) {
      flushPara()
      if (inOl) {
        html += '</ol>'
        inOl = false
      }
      if (!inUl) {
        html += '<ul style="margin:4px 0 4px 18px;padding:0;">'
        inUl = true
      }
      html += `<li style="margin-bottom:2px;font-size:13px;">${applyInline(ulMatch[2])}</li>`
      continue
    }
    // 有序清單
    const olMatch = line.match(/^(\s*)\d+\.\s+(.+)$/)
    if (olMatch) {
      flushPara()
      if (inUl) {
        html += '</ul>'
        inUl = false
      }
      if (!inOl) {
        html += '<ol style="margin:4px 0 4px 18px;padding:0;">'
        inOl = true
      }
      html += `<li style="margin-bottom:2px;font-size:13px;">${applyInline(olMatch[2])}</li>`
      continue
    }
    closeList()
    if (line === '') {
      flushPara()
    } else {
      paraLines.push(applyInline(line))
    }
  }
  flushPara()
  closeList()
  if (inCodeBlock)
    html += `<pre style="background:#1e293b;color:#e2e8f0;border-radius:6px;padding:10px 14px;font-family:monospace;font-size:12px;margin:6px 0;white-space:pre-wrap;">${escHtml(codeLines.join('\n'))}</pre>`
  if (inTable) {
    tableHtml += '</tbody></table>'
    html += tableHtml
  }
  return html
}

// ===== 圖表區塊（長條圖 / 折線圖 / 圓餅圖）=====
const CHART_COLORS = [
  '#6366f1',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#3b82f6',
  '#8b5cf6',
  '#ec4899',
  '#14b8a6',
]

interface ChartBlockProps {
  chartData: ChartData
}

function ChartBlock({ chartData }: ChartBlockProps) {
  const { chart_type, title, data } = chartData
  const labels = data.map((d) => d.label)
  const values = data.map((d) => d.value)
  const max = Math.max(...values, 1)
  const W = 340
  const H = 160

  let svgContent: React.ReactNode = null
  let legendContent: React.ReactNode = null

  if (chart_type === 'bar') {
    const barW = Math.floor((W - 40) / Math.max(labels.length, 1)) - 6
    const barArea = H - 30
    svgContent = (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', overflow: 'visible' }}>
        <line x1="38" y1="10" x2="38" y2={H - 20} stroke="#e2e8f0" strokeWidth="1" />
        <text x="36" y={H - 20} textAnchor="end" fontSize="9" fill="#94a3b8">
          0
        </text>
        <text x="36" y="14" textAnchor="end" fontSize="9" fill="#94a3b8">
          {max}
        </text>
        {labels.map((lbl, i) => {
          const bh = Math.round((values[i] / max) * barArea)
          const x = 40 + i * (barW + 6)
          const y = H - 20 - bh
          return (
            <g key={i}>
              <rect
                x={x}
                y={y}
                width={barW}
                height={bh}
                fill={CHART_COLORS[i % CHART_COLORS.length]}
                rx="2"
              />
              <text x={x + barW / 2} y={H - 4} textAnchor="middle" fontSize="10" fill="#475569">
                {String(lbl).slice(0, 6)}
              </text>
              <text x={x + barW / 2} y={y - 3} textAnchor="middle" fontSize="10" fill="#1e293b">
                {values[i]}
              </text>
            </g>
          )
        })}
      </svg>
    )
  } else if (chart_type === 'line') {
    const pts = labels.map((_, i) => ({
      px: 40 + i * ((W - 50) / Math.max(labels.length - 1, 1)),
      py: 10 + ((max - values[i]) / max) * (H - 40),
      lbl: labels[i],
      val: values[i],
    }))
    const polylinePoints = pts.map((p) => `${p.px},${p.py}`).join(' ')
    svgContent = (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', overflow: 'visible' }}>
        <line x1="38" y1="10" x2="38" y2={H - 20} stroke="#e2e8f0" strokeWidth="1" />
        <text x="36" y={H - 20} textAnchor="end" fontSize="9" fill="#94a3b8">
          0
        </text>
        <text x="36" y="14" textAnchor="end" fontSize="9" fill="#94a3b8">
          {max}
        </text>
        <polyline points={polylinePoints} fill="none" stroke={CHART_COLORS[0]} strokeWidth="2" />
        {pts.map((p, i) => (
          <g key={i}>
            <circle cx={p.px} cy={p.py} r="3" fill={CHART_COLORS[0]} />
            <text x={p.px} textAnchor="middle" y={H - 4} fontSize="10" fill="#475569">
              {String(p.lbl).slice(0, 6)}
            </text>
            <text x={p.px} y={p.py - 6} textAnchor="middle" fontSize="10" fill="#1e293b">
              {p.val}
            </text>
          </g>
        ))}
      </svg>
    )
  } else if (chart_type === 'pie') {
    const total = values.reduce((a, b) => a + b, 0) || 1
    const cx = 80
    const cy = 75
    const r = 60
    // Pre-compute start angles to avoid mutating variable inside map
    const startAngles = values.reduce<number[]>((acc, v, i) => {
      if (i === 0) return [-Math.PI / 2]
      return [...acc, acc[i - 1] + (values[i - 1] / total) * 2 * Math.PI]
    }, [])
    const slices: React.ReactNode[] = values.map((v, i) => {
      const sliceAngle = (v / total) * 2 * Math.PI
      const startAngle = startAngles[i]
      const x1 = cx + r * Math.cos(startAngle)
      const y1 = cy + r * Math.sin(startAngle)
      const x2 = cx + r * Math.cos(startAngle + sliceAngle)
      const y2 = cy + r * Math.sin(startAngle + sliceAngle)
      const large = sliceAngle > Math.PI ? 1 : 0
      const path = `M${cx},${cy} L${x1},${y1} A${r},${r} 0 ${large} 1 ${x2},${y2} Z`
      return <path key={i} d={path} fill={CHART_COLORS[i % CHART_COLORS.length]} />
    })
    svgContent = (
      <svg viewBox="0 0 160 150" style={{ width: '100%', overflow: 'visible' }}>
        {slices}
      </svg>
    )
    legendContent = (
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: '8px 14px', mt: '6px' }}>
        {labels.map((lbl, i) => (
          <Box
            key={i}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              fontSize: 11,
              color: '#475569',
            }}
          >
            <Box
              sx={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                bgcolor: CHART_COLORS[i % CHART_COLORS.length],
                flexShrink: 0,
              }}
            />
            {String(lbl)}（{values[i]}）
          </Box>
        ))}
      </Box>
    )
  }

  return (
    <Box
      sx={{
        mt: '8px',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        p: '10px 12px 8px',
        bgcolor: '#fafbff',
      }}
    >
      <Typography sx={{ fontSize: 12, fontWeight: 600, color: '#1e293b', mb: '8px' }}>
        {title}
      </Typography>
      {svgContent}
      {legendContent}
    </Box>
  )
}

// ===== AI 訊息泡泡（支援 Markdown + 複製按鈕）=====
interface AiBubbleProps {
  content: string
  isMobile?: boolean
  chartData?: ChartData | null
}

function AiBubble({ content, isMobile = false, chartData }: AiBubbleProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [isCopied, setIsCopied] = useState(false)
  const [hoverY, setHoverY] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  function handleMouseEnter(e: React.MouseEvent<HTMLDivElement>) {
    const rect = containerRef.current?.getBoundingClientRect()
    if (rect) setHoverY(e.clientY - rect.top)
    setIsHovered(true)
  }

  function handleCopy() {
    navigator.clipboard.writeText(stripMarkdown(content)).then(() => {
      setIsCopied(true)
      setTimeout(() => setIsCopied(false), 1500)
    })
  }

  if (isMobile) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, maxWidth: '90%' }}>
        <Box sx={{ flex: 1 }}>
          <Box
            sx={{
              bgcolor: '#f1f5f9',
              color: '#1e293b',
              px: 2,
              py: 1.25,
              borderRadius: '16px 16px 16px 4px',
              fontSize: 14,
              lineHeight: 1.6,
              '& strong': { fontWeight: 700 },
              '& pre': { overflowX: 'auto' },
            }}
            dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
          />
          {chartData && <ChartBlock chartData={chartData} />}
        </Box>
        <IconButton
          size="small"
          onClick={handleCopy}
          sx={{
            flexShrink: 0,
            color: isCopied ? '#22c55e' : '#cbd5e1',
            width: 24,
            height: 24,
            mt: 0.5,
            '&:active': { color: '#4f46e5' },
          }}
        >
          {isCopied ? (
            <CheckIcon sx={{ fontSize: 13 }} />
          ) : (
            <ContentCopyIcon sx={{ fontSize: 13 }} />
          )}
        </IconButton>
      </Box>
    )
  }

  return (
    <Box
      ref={containerRef}
      sx={{ display: 'flex', alignItems: 'flex-start' }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* 左側複製按鈕欄：與滑鼠進入高度對齊 */}
      <Box sx={{ width: 30, flexShrink: 0, position: 'relative', alignSelf: 'stretch' }}>
        {isHovered && (
          <Tooltip title={isCopied ? '已複製' : '複製'} placement="top">
            <IconButton
              size="small"
              onClick={handleCopy}
              sx={{
                position: 'absolute',
                top: Math.max(0, hoverY - 13),
                left: 2,
                zIndex: 1,
                bgcolor: 'white',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                width: 26,
                height: 26,
                color: isCopied ? '#22c55e' : '#64748b',
                '&:hover': { color: '#4f46e5', borderColor: '#c7d2fe' },
              }}
            >
              {isCopied ? (
                <CheckIcon sx={{ fontSize: 14 }} />
              ) : (
                <ContentCopyIcon sx={{ fontSize: 14 }} />
              )}
            </IconButton>
          </Tooltip>
        )}
      </Box>
      <Box sx={{ maxWidth: '90%' }}>
        <Box
          sx={{
            bgcolor: '#f1f5f9',
            color: '#1e293b',
            px: 2,
            py: 1.25,
            borderRadius: '16px 16px 16px 4px',
            fontSize: 14,
            lineHeight: 1.6,
            '& strong': { fontWeight: 700 },
            '& pre': { overflowX: 'auto' },
          }}
          dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
        />
        {chartData && <ChartBlock chartData={chartData} />}
      </Box>
    </Box>
  )
}

// ===== 工具呼叫提示列 =====
interface ToolCallingRowProps {
  toolName: string
}

function ToolCallingRow({ toolName }: ToolCallingRowProps) {
  const label = toolName === 'render_chart' ? '正在產生圖表…' : `正在使用：${toolName}`
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        fontSize: 12,
        color: '#64748b',
        py: '4px',
        alignSelf: 'flex-start',
      }}
    >
      <Box
        sx={{
          width: 8,
          height: 8,
          bgcolor: '#6366f1',
          borderRadius: '50%',
          flexShrink: 0,
          animation: 'toolPulse 1s infinite',
          '@keyframes toolPulse': {
            '0%, 100%': { opacity: 1 },
            '50%': { opacity: 0.3 },
          },
        }}
      />
      <Typography sx={{ fontSize: 12, color: '#64748b' }}>{label}</Typography>
    </Box>
  )
}

// ===== 思考中動畫 =====
const THINKING_LABELS = ['思考中', '用力思考']

function ThinkingIndicator() {
  const [tick, setTick] = useState(0)
  const dotCount = (tick % 20) + 1
  const labelIdx = Math.floor(tick / 20) % THINKING_LABELS.length

  useEffect(() => {
    const timer = setInterval(() => setTick((t) => t + 1), 200)
    return () => clearInterval(timer)
  }, [])

  return (
    <Box
      sx={{
        bgcolor: '#f1f5f9',
        px: 2,
        py: 1.25,
        borderRadius: '16px 16px 16px 4px',
        display: 'inline-flex',
        alignItems: 'baseline',
      }}
    >
      <Typography
        component="span"
        sx={{
          fontSize: 13,
          fontWeight: 700,
          animation: 'thinkingColor 1.35s ease-in-out infinite',
          '@keyframes thinkingColor': {
            '0%, 100%': { color: '#94a3b8' },
            '50%': { color: '#1e293b' },
          },
        }}
      >
        {THINKING_LABELS[labelIdx]}
        {'.'.repeat(dotCount)}
      </Typography>
    </Box>
  )
}

// ===== 503 錯誤提示列 =====
interface ErrorRowProps {
  hasImage: boolean
  onRetry: () => void
}

function ErrorRow({ hasImage, onRetry }: ErrorRowProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 1.25,
        bgcolor: '#fef2f2',
        border: '1px solid #fecaca',
        borderRadius: '8px',
        px: 1.75,
        py: 1,
        fontSize: 13,
        color: '#dc2626',
      }}
    >
      <Typography sx={{ fontSize: 13, color: '#dc2626', flex: 1 }}>
        {hasImage
          ? '⚠ AI 服務暫時無法使用（503）（原訊息含圖片，請重新上傳後再傳送）'
          : '⚠ AI 服務暫時無法使用（503）'}
      </Typography>
      {!hasImage && (
        <Button
          size="small"
          variant="outlined"
          onClick={onRetry}
          sx={{
            fontSize: 12,
            height: 26,
            borderRadius: '6px',
            borderColor: '#fca5a5',
            color: '#dc2626',
            flexShrink: 0,
            '&:hover': { bgcolor: '#fef2f2' },
          }}
        >
          重新傳送
        </Button>
      )}
    </Box>
  )
}

// ===== 主元件 =====
export default function FnAiPartnerChat({ partner, onBack }: Props) {
  const isMobileInput = useMediaQuery('(max-width:600px)')
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [inputText, setInputText] = useState('')
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [sendError, setSendError] = useState<{ message: string; hasImage: boolean } | null>(null)
  const [isConfirmNewOpen, setIsConfirmNewOpen] = useState(false)
  const [isShowSuggestions, setIsShowSuggestions] = useState(false)
  const [helpAnchor, setHelpAnchor] = useState<HTMLButtonElement | null>(null)
  const helpButtonRef = useRef<HTMLButtonElement>(null)
  // 記錄是否已有首次 AI 回覆（用於建議 Chip 自動展開）
  const [isFirstAiReplyDone, setIsFirstAiReplyDone] = useState(false)
  // 記錄最後一則使用者訊息（用於 503 重試）
  const lastUserMsgRef = useRef<{ text: string; image: File | null; hasImage: boolean } | null>(
    null
  )
  // 捲到最新浮動按鈕
  const [isShowScrollBtn, setIsShowScrollBtn] = useState(false)
  // 工具呼叫提示（streaming 期間顯示）
  const [toolCallingName, setToolCallingName] = useState<string | null>(null)

  // 語音輸入狀態
  const [isVoiceSupported, setIsVoiceSupported] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textInputRef = useRef<HTMLTextAreaElement>(null)

  const queryClient = useQueryClient()
  const { data: historyData, isLoading: isHistoryLoading } = useAiPartnerHistoryQuery(partner.id)
  const newChat = useNewAiPartnerChat()
  const sendMessage = useSendAiPartnerMessage()

  const isLoading = isHistoryLoading || newChat.isPending

  // 將輸入框 focus 的工具函式
  const focusInput = useCallback(() => {
    // 短暫延遲確保 DOM 更新後 focus
    setTimeout(() => {
      textInputRef.current?.focus()
    }, 50)
  }, [])

  // 語音輸入初始化（僅瀏覽器支援時顯示麥克風按鈕）
  useEffect(() => {
    const SpeechRecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognitionCtor) return
    setIsVoiceSupported(true)
    const rec = new SpeechRecognitionCtor()
    rec.lang = 'zh-TW'
    rec.interimResults = false
    rec.continuous = false
    rec.onresult = (e: SpeechRecognitionEvent) => {
      const transcript = e.results[0][0].transcript
      setInputText((prev) => (prev ? prev + ' ' + transcript : transcript))
    }
    rec.onend = () => {
      setIsRecording(false)
    }
    rec.onerror = () => {
      setIsRecording(false)
    }
    recognitionRef.current = rec
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.onresult = null
        recognitionRef.current.onend = null
        recognitionRef.current.onerror = null
      }
    }
  }, [])

  // 1. 進入對話畫面時 focus 輸入框
  useEffect(() => {
    if (isInitialized) {
      focusInput()
    }
  }, [isInitialized, focusInput])

  // Initialize chat on history load
  useEffect(() => {
    if (!historyData || isInitialized) return
    if (historyData.conversation_id) {
      startTransition(() => {
        setConversationId(historyData.conversation_id)
        setMessages(historyData.messages)
        setSuggestions(historyData.suggestions)
        setIsInitialized(true)
      })
    } else {
      // No existing conversation — start new one
      newChat.mutate(partner.id, {
        onSuccess: (data) => {
          startTransition(() => {
            setConversationId(data.conversation_id)
            setMessages(data.messages)
            setSuggestions(data.suggestions)
            setIsInitialized(true)
          })
          setTimeout(() => {
            if (helpButtonRef.current) setHelpAnchor(helpButtonRef.current)
          }, 100)
          setTimeout(() => {
            queryClient.invalidateQueries({ queryKey: ['aiPartnerHistory', partner.id] })
          }, 4000)
        },
        onError: (err) => {
          const msg = err instanceof Error ? err.message : 'AI 服務暫時無法使用，請稍後再試'
          setSendError({ message: msg || 'AI 服務暫時無法使用，請稍後再試', hasImage: false })
        },
      })
    }
  }, [historyData, isInitialized, partner.id]) // eslint-disable-line react-hooks/exhaustive-deps

  // 捲到最新訊息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isSending, isLoading])

  // 新對話後建議由背景任務非同步產生，historyData 重新抓取後若有建議則更新
  useEffect(() => {
    if (!isInitialized) return
    if (!historyData?.suggestions?.length) return
    if (suggestions.length > 0) return
    setSuggestions(historyData.suggestions)
  }, [historyData?.suggestions]) // eslint-disable-line react-hooks/exhaustive-deps

  // 捲動監聽：更新「捲到最新」浮動按鈕顯示狀態
  const handleMessagesScroll = useCallback(() => {
    const el = messagesContainerRef.current
    if (!el) return
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 30
    setIsShowScrollBtn(!atBottom)
  }, [])

  function handleScrollToBottom() {
    messagesContainerRef.current?.scrollTo({
      top: messagesContainerRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }

  function handleImageSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null
    if (!file) return
    setSelectedImage(file)
    const reader = new FileReader()
    reader.onload = () => {
      setImagePreviewUrl(reader.result as string)
      // 3. 圖片選取完成後（FileReader 讀取完成）focus 輸入框
      focusInput()
    }
    reader.readAsDataURL(file)
    // 同步更新 objectURL 供預覽（FileReader 非同步，用 createObjectURL 立即顯示）
    setImagePreviewUrl(URL.createObjectURL(file))
  }

  function handleRemoveImage() {
    setSelectedImage(null)
    if (imagePreviewUrl) URL.revokeObjectURL(imagePreviewUrl)
    setImagePreviewUrl(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function handleChipClick(text: string) {
    doSend(text, null)
    focusInput()
  }

  async function handleSend() {
    if (!inputText.trim() && !selectedImage) return
    if (!conversationId) return
    doSend(inputText, selectedImage)
  }

  async function doSend(text: string, image: File | null) {
    if (!text.trim() && !image) return
    if (!conversationId) return

    const hadImage = !!image

    lastUserMsgRef.current = { text, image, hasImage: hadImage }

    const userMessage: ChatMessage = {
      role: 'user',
      content: text,
      image_url: image ? imagePreviewUrl : null,
      created_at: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setSuggestions([])
    setIsShowSuggestions(false)
    setInputText('')
    setSelectedImage(null)
    if (imagePreviewUrl && !image) URL.revokeObjectURL(imagePreviewUrl)
    setImagePreviewUrl(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
    setIsSending(true)
    setSendError(null)

    // 若後端回傳含 chart_data，先顯示工具呼叫提示列
    sendMessage.mutate(
      {
        partner_id: partner.id,
        conversation_id: conversationId,
        message: text || undefined,
        image: image,
      },
      {
        onSuccess: (data) => {
          // 若有 chart_data，先短暫顯示 render_chart 工具提示列
          if (data.chart_data) {
            setToolCallingName('render_chart')
            setTimeout(() => {
              setToolCallingName(null)
              const aiMessage: ChatMessage = {
                role: 'assistant',
                content: data.content,
                image_url: null,
                created_at: new Date().toISOString(),
                chart_data: data.chart_data,
              }
              setMessages((prev) => [...prev, aiMessage])
              setSuggestions(data.suggestions)
              setIsSending(false)
              if (!isFirstAiReplyDone) {
                setIsFirstAiReplyDone(true)
              }
              focusInput()
            }, 600)
          } else {
            const aiMessage: ChatMessage = {
              role: 'assistant',
              content: data.content,
              image_url: null,
              created_at: new Date().toISOString(),
              chart_data: null,
            }
            setMessages((prev) => [...prev, aiMessage])
            setSuggestions(data.suggestions)
            setIsSending(false)
            if (!isFirstAiReplyDone) {
              setIsFirstAiReplyDone(true)
            }
            // 2. AI 回覆完成後 focus 輸入框
            focusInput()
          }
        },
        onError: (err: Error & { status?: number }) => {
          setToolCallingName(null)
          if (err.status === 503) {
            setSendError({
              message: err.message || 'AI 服務暫時無法使用，請稍後再試',
              hasImage: hadImage,
            })
          }
          setIsSending(false)
        },
      }
    )
  }

  function handleRetry() {
    if (!lastUserMsgRef.current) return
    const { text, image } = lastUserMsgRef.current
    setSendError(null)
    doSend(text, image)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLDivElement>) {
    if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function handleBack() {
    handleRemoveImage()
    onBack()
  }

  function handleToggleVoice() {
    if (!recognitionRef.current) return
    if (isRecording) {
      recognitionRef.current.stop()
    } else {
      setIsRecording(true)
      recognitionRef.current.start()
    }
  }

  function handleConfirmNewChat() {
    setIsConfirmNewOpen(false)
    setMessages([])
    setSuggestions([])
    setConversationId(null)
    setSendError(null)
    setIsFirstAiReplyDone(false)
    lastUserMsgRef.current = null
    newChat.mutate(partner.id, {
      onSuccess: (data) => {
        setConversationId(data.conversation_id)
        setMessages(data.messages)
        setSuggestions(data.suggestions)
        setInputText('')
        setIsShowSuggestions(false)
        handleRemoveImage()
        if (helpButtonRef.current) setHelpAnchor(helpButtonRef.current)
        setTimeout(() => {
          queryClient.invalidateQueries({ queryKey: ['aiPartnerHistory', partner.id] })
        }, 4000)
      },
      onError: (err) => {
        const msg = err instanceof Error ? err.message : '建立新對話失敗，請稍後再試'
        setSendError({ message: msg, hasImage: false })
      },
    })
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 40px - 28px)' }}>
      {/* 7. Top bar — 修正底部分隔線與下方元素視覺重疊：加 borderBottom + mb */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          pb: 1.25,
          mb: 0.5,
          borderBottom: '1px solid #e2e8f0',
          flexShrink: 0,
          gap: 1,
        }}
      >
        <Typography sx={{ fontSize: 15, fontWeight: 700, color: '#1e293b', flex: 1 }}>
          {partner.name}
        </Typography>
        <Button
          size="small"
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={handleBack}
          sx={{
            fontSize: 12,
            height: 28,
            borderRadius: '3px',
            borderColor: '#cbd5e1',
            color: '#475569',
            '&:hover': { bgcolor: '#f1f5f9' },
          }}
        >
          返回
        </Button>
        <Button
          size="small"
          variant="outlined"
          onClick={() => setIsConfirmNewOpen(true)}
          sx={{
            fontSize: 12,
            height: 28,
            borderRadius: '3px',
            borderColor: '#6366f1',
            color: '#6366f1',
            '&:hover': { bgcolor: '#f0f0ff' },
          }}
        >
          新對話
        </Button>
      </Box>

      {/* 6. Messages area — position:relative 支援浮動按鈕定位 */}
      <Box
        sx={{
          flex: 1,
          position: 'relative',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Box
          ref={messagesContainerRef}
          onScroll={handleMessagesScroll}
          sx={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 1.5,
            py: 1,
            px: 0.5,
          }}
        >
          {messages.map((msg, idx) => (
            <Box
              key={idx}
              sx={{
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              {msg.role === 'assistant' ? (
                // 1. AI 回覆：Markdown 渲染 + 4. 複製按鈕 + 圖表區塊
                <AiBubble
                  content={msg.content}
                  isMobile={isMobileInput}
                  chartData={msg.chart_data}
                />
              ) : (
                // 使用者訊息：純文字
                <Box
                  sx={{
                    maxWidth: '85%',
                    bgcolor: '#6366f1',
                    color: 'white',
                    px: 2,
                    py: 1.25,
                    borderRadius: '16px 16px 4px 16px',
                    fontSize: 14,
                    lineHeight: 1.6,
                  }}
                >
                  {msg.image_url && (
                    <Box
                      component="img"
                      src={msg.image_url}
                      sx={{
                        width: 120,
                        height: 120,
                        objectFit: 'cover',
                        borderRadius: 1,
                        mb: 0.75,
                        display: 'block',
                      }}
                    />
                  )}
                  <Typography sx={{ fontSize: 13, whiteSpace: 'pre-wrap', color: 'inherit' }}>
                    {msg.content}
                  </Typography>
                </Box>
              )}
            </Box>
          ))}

          {/* AI loading indicator */}
          {isSending && !toolCallingName && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
              <ThinkingIndicator />
            </Box>
          )}

          {/* 工具呼叫提示列（render_chart 顯示「正在產生圖表…」）*/}
          {toolCallingName && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
              <ToolCallingRow toolName={toolCallingName} />
            </Box>
          )}

          {/* 3. 503 錯誤提示列 */}
          {sendError && <ErrorRow hasImage={sendError.hasImage} onRetry={handleRetry} />}

          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress size={28} />
            </Box>
          )}

          <div ref={messagesEndRef} />
        </Box>

        {/* 6. 「↓ 捲到最新」浮動按鈕 */}
        {isShowScrollBtn && (
          <Button
            size="small"
            startIcon={<KeyboardArrowDownIcon />}
            onClick={handleScrollToBottom}
            sx={{
              position: 'absolute',
              bottom: 14,
              right: 14,
              zIndex: 10,
              bgcolor: 'white',
              border: '1px solid #c7d2fe',
              borderRadius: '20px',
              color: '#4f46e5',
              fontSize: 12,
              px: 1.75,
              py: 0.625,
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
              '&:hover': { bgcolor: '#eff6ff' },
            }}
          >
            捲到最新
          </Button>
        )}
      </Box>

      {/* 5. 建議問題清單（展開時顯示） */}
      {suggestions.length > 0 && !isSending && isShowSuggestions && (
        <Box
          sx={{
            flexShrink: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: 0.75,
            pb: 0.75,
          }}
        >
          {suggestions.map((s, idx) => (
            <Chip
              key={idx}
              label={s}
              size="small"
              onClick={() => {
                handleChipClick(s)
                // 4. Chip 點擊後送出後 focus 輸入框（doSend 結束後由 focusInput 處理）
              }}
              sx={{
                fontSize: 12,
                bgcolor: '#f0f0ff',
                color: '#4f46e5',
                border: '1px solid #c7d2fe',
                cursor: 'pointer',
                '&:hover': { bgcolor: '#e0e7ff' },
              }}
            />
          ))}
        </Box>
      )}

      {/* Input area — 桌機：橫向一列；手機（≤600px）：垂直分層 */}
      <Box
        sx={{
          flexShrink: 0,
          pt: 0.5,
          display: 'flex',
          flexDirection: isMobileInput ? 'column' : 'row',
          alignItems: isMobileInput ? 'stretch' : 'flex-end',
          gap: isMobileInput ? '6px' : 1,
        }}
      >
        {/* 隱藏 file input（在任何模式下都保留） */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={handleImageSelect}
        />

        {/* Popover（操作技巧說明，在任何模式下都保留） */}
        <Popover
          open={Boolean(helpAnchor)}
          anchorEl={helpAnchor}
          onClose={() => setHelpAnchor(null)}
          anchorOrigin={{ vertical: 'top', horizontal: 'left' }}
          transformOrigin={{ vertical: 'bottom', horizontal: 'left' }}
          slotProps={{ paper: { sx: { borderRadius: 2, boxShadow: 3, p: 2, maxWidth: 280 } } }}
        >
          <Typography sx={{ fontSize: 13, fontWeight: 700, color: '#1e293b', mb: 1.5 }}>
            操作技巧
          </Typography>
          {[
            { keys: 'Shift + Enter', desc: '送出訊息' },
            { keys: 'Enter', desc: '換行' },
            { keys: '📷 圖片圖示', desc: '上傳圖片，AI 可分析圖片內容' },
            { keys: '💡 燈泡圖示', desc: '開啟 AI 推薦的下一步問題' },
            { keys: '新對話', desc: '清除目前記錄，重新開始對話' },
          ].map(({ keys, desc }) => (
            <Box key={keys} sx={{ display: 'flex', gap: 1, mb: 1, alignItems: 'flex-start' }}>
              <Typography
                sx={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#6366f1',
                  bgcolor: '#f0f0ff',
                  px: 0.75,
                  py: 0.25,
                  borderRadius: 1,
                  whiteSpace: 'nowrap',
                  lineHeight: 1.8,
                }}
              >
                {keys}
              </Typography>
              <Typography sx={{ fontSize: 12, color: '#475569', lineHeight: 1.8 }}>
                {desc}
              </Typography>
            </Box>
          ))}
        </Popover>

        {/* 第一列：桌機含圖片按鈕；手機含圖片按鈕 + 麥克風按鈕 + 輸入框 */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: 1,
            flex: isMobileInput ? undefined : 1,
          }}
        >
          {/* 圖片按鈕：桌機與手機第一列均顯示 */}
          <IconButton
            size="small"
            onClick={() => fileInputRef.current?.click()}
            sx={{ color: '#94a3b8', '&:hover': { color: '#6366f1', bgcolor: '#f0f0ff' } }}
          >
            <ImageIcon fontSize="small" />
          </IconButton>

          {/* 麥克風按鈕：僅手機模式 + 瀏覽器支援時顯示 */}
          {isMobileInput && isVoiceSupported && (
            <Tooltip title={isRecording ? '停止錄音' : '語音輸入'} placement="top">
              <IconButton
                size="small"
                onClick={handleToggleVoice}
                sx={{
                  color: isRecording ? '#ef4444' : '#94a3b8',
                  bgcolor: isRecording ? '#fef2f2' : 'transparent',
                  animation: isRecording ? 'micPulse 1s infinite' : 'none',
                  '@keyframes micPulse': {
                    '0%, 100%': { opacity: 1 },
                    '50%': { opacity: 0.5 },
                  },
                  '&:hover': {
                    color: isRecording ? '#dc2626' : '#6366f1',
                    bgcolor: isRecording ? '#fef2f2' : '#f0f0ff',
                  },
                }}
              >
                <MicNoneIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}

          <Box
            sx={{
              flex: 1,
              border: '1px solid #cbd5e1',
              borderRadius: '20px',
              bgcolor: 'white',
              overflow: 'hidden',
              '&:focus-within': { borderColor: '#6366f1' },
            }}
          >
            {imagePreviewUrl && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 1.5, pt: 1 }}>
                <Box
                  component="img"
                  src={imagePreviewUrl}
                  sx={{
                    width: 56,
                    height: 56,
                    objectFit: 'cover',
                    borderRadius: 1,
                    border: '1px solid #e2e8f0',
                  }}
                />
                <IconButton
                  size="small"
                  onClick={handleRemoveImage}
                  sx={{
                    bgcolor: '#94a3b8',
                    color: 'white',
                    width: 18,
                    height: 18,
                    '&:hover': { bgcolor: '#64748b' },
                  }}
                >
                  <CloseIcon sx={{ fontSize: 12 }} />
                </IconButton>
              </Box>
            )}
            <TextField
              multiline
              maxRows={4}
              fullWidth
              placeholder="輸入訊息…"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isSending || !isInitialized}
              variant="standard"
              inputRef={textInputRef}
              slotProps={{ input: { disableUnderline: true } }}
              sx={{
                '& .MuiInputBase-root': { px: 1.5, py: 1, fontSize: 14 },
              }}
            />
          </Box>
        </Box>

        {/* 第二列（手機：燈泡 + 送出靠右）／同列（桌機：help + 燈泡 + 送出） */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            justifyContent: isMobileInput ? 'flex-end' : 'flex-start',
          }}
        >
          {/* help 按鈕：手機模式隱藏，桌機模式顯示 */}
          <IconButton
            ref={helpButtonRef}
            size="small"
            onClick={(e) => setHelpAnchor(e.currentTarget)}
            sx={{
              color: '#94a3b8',
              display: isMobileInput ? 'none' : 'inline-flex',
              '&:hover': { color: '#6366f1', bgcolor: '#f0f0ff' },
            }}
          >
            <HelpOutlineIcon fontSize="small" />
          </IconButton>

          {suggestions.length > 0 && !isSending && (
            <IconButton
              size="small"
              onClick={() => setIsShowSuggestions((v) => !v)}
              sx={{
                color: isShowSuggestions ? '#6366f1' : '#94a3b8',
                bgcolor: isShowSuggestions ? '#f0f0ff' : 'transparent',
                '&:hover': { color: '#6366f1', bgcolor: '#f0f0ff' },
              }}
            >
              <TipsAndUpdatesOutlinedIcon fontSize="small" />
            </IconButton>
          )}

          <IconButton
            onClick={handleSend}
            disabled={(!inputText.trim() && !selectedImage) || isSending || !isInitialized}
            sx={{
              bgcolor: '#6366f1',
              color: 'white',
              width: 36,
              height: 36,
              '&:hover': { bgcolor: '#4f46e5' },
              '&.Mui-disabled': { bgcolor: '#e2e8f0', color: '#94a3b8' },
            }}
          >
            <SendIcon fontSize="small" />
          </IconButton>
        </Box>
      </Box>

      {/* Confirm new chat dialog */}
      <Dialog
        open={isConfirmNewOpen}
        onClose={() => setIsConfirmNewOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 700, fontSize: 16 }}>新對話</DialogTitle>
        <DialogContent>
          <Typography sx={{ fontSize: 14 }}>確定要清除目前對話並重新開始嗎？</Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => setIsConfirmNewOpen(false)} sx={{ color: '#64748b' }}>
            取消
          </Button>
          <Button
            onClick={handleConfirmNewChat}
            variant="contained"
            sx={{ bgcolor: '#6366f1', '&:hover': { bgcolor: '#4f46e5' } }}
          >
            確認
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
