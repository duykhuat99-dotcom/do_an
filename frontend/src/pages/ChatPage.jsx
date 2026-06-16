import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined'
import ChatMessage from '../components/ChatMessage'
import ConversationSidebar from '../components/ConversationSidebar'
import api from '../services/api'

const SUGGESTIONS = [
  'Doanh thu theo chi nhánh năm 2024?',
  'Top 10 sản phẩm bán chạy nhất?',
  'Cơ cấu doanh thu theo danh mục sản phẩm?',
  'Doanh thu theo từng tháng trong năm 2024?',
]

// Sinh session_id mới cho mỗi cuộc trò chuyện.
function newSessionId() {
  return `web-${Date.now().toString(16)}-${Math.random().toString(16).slice(2, 8)}`
}

// Chuyển bản ghi lịch sử (mới→cũ) thành danh sách tin nhắn (cũ→mới).
// Khôi phục đầy đủ SQL + biểu đồ + insight đã lưu.
function historyToMessages(rows) {
  return [...rows].reverse().map((r) => {
    if (r.role === 'user') return { role: 'user', content: r.question || '' }
    const hasData = r.generated_sql || r.chart || r.insight
    return {
      role: 'assistant',
      content: r.answer || '',
      data: hasData
        ? { sql: r.generated_sql, chart: r.chart || null, insight: r.insight || null }
        : null,
    }
  })
}

export default function ChatPage() {
  const [sessions, setSessions] = useState([])
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [activeId, setActiveId] = useState(newSessionId)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const endRef = useRef(null)

  const refreshSessions = useCallback(async () => {
    setLoadingSessions(true)
    try {
      const data = await api.listSessions()
      setSessions(data.sessions || [])
    } catch {
      /* DB có thể chưa sẵn sàng — bỏ qua, danh sách rỗng */
    } finally {
      setLoadingSessions(false)
    }
  }, [])

  useEffect(() => {
    refreshSessions()
  }, [refreshSessions])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  function newChat() {
    setActiveId(newSessionId())
    setMessages([])
    setInput('')
    setSuggestions([])
  }

  async function selectSession(id) {
    if (id === activeId) return
    setActiveId(id)
    setMessages([])
    setSuggestions([])
    setLoadingHistory(true)
    try {
      const data = await api.history(id, 100)
      setMessages(historyToMessages(data.history || []))
    } catch (e) {
      setMessages([{ role: 'assistant', content: `Không tải được lịch sử: ${e.message}` }])
    } finally {
      setLoadingHistory(false)
    }
  }

  async function send(question) {
    const q = (question ?? input).trim()
    if (!q || loading) return
    setInput('')
    setSuggestions([])
    setMessages((m) => [...m, { role: 'user', content: q }])
    setLoading(true)
    try {
      const data = await api.chat({ question: q, session_id: activeId })
      // animate: bật hiệu ứng gõ chữ cho câu trả lời mới
      setMessages((m) => [...m, { role: 'assistant', content: data.answer, data, animate: true }])
      refreshSessions() // cập nhật danh sách (tạo mới / đổi thời gian)
      fetchSuggestions(q, data.answer)
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', content: `Lỗi: ${e.message}`, data: null }])
    } finally {
      setLoading(false)
    }
  }

  async function fetchSuggestions(question, answer) {
    try {
      const r = await api.suggestQuestions(question, answer)
      setSuggestions(r.suggestions || [])
    } catch {
      setSuggestions([])
    }
  }

  function handleFeedback(index, rating) {
    const question = messages[index - 1]?.content || null
    const answer = messages[index]?.content || null
    api.sendFeedback({ rating, question, answer, session_id: activeId }).catch(() => {})
  }

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 160px)', gap: 0 }}>
      <ConversationSidebar
        sessions={sessions}
        activeId={activeId}
        onSelect={selectSession}
        onNew={newChat}
        loading={loadingSessions}
      />

      <Stack sx={{ flex: 1, pl: 2, minWidth: 0 }}>
        <Paper variant="outlined" sx={{ flex: 1, p: 2, overflowY: 'auto', bgcolor: 'grey.50' }}>
          {loadingHistory && (
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
              <CircularProgress size={16} />
              <Typography variant="body2" color="text.secondary">
                Đang tải lịch sử...
              </Typography>
            </Stack>
          )}

          {messages.length === 0 && !loading && !loadingHistory && (
            <Box sx={{ textAlign: 'center', mt: 4 }}>
              <Typography variant="h6" gutterBottom>
                Hỏi gì đó về dữ liệu DataMart 👋
              </Typography>
              <Stack direction="row" spacing={1} justifyContent="center" flexWrap="wrap" useFlexGap>
                {SUGGESTIONS.map((s) => (
                  <Button key={s} size="small" variant="outlined" onClick={() => send(s)}>
                    {s}
                  </Button>
                ))}
              </Stack>
            </Box>
          )}

          {messages.map((m, i) => (
            <ChatMessage
              key={i}
              role={m.role}
              content={m.content}
              data={m.data}
              animate={m.animate}
              onFeedback={m.role === 'assistant' && m.data ? (r) => handleFeedback(i, r) : undefined}
            />
          ))}
          {loading && <ChatMessage role="assistant" loading />}
          <div ref={endRef} />
        </Paper>

        {suggestions.length > 0 && !loading && (
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap alignItems="center" sx={{ mt: 1 }}>
            <LightbulbOutlinedIcon fontSize="small" color="warning" />
            <Typography variant="caption" color="text.secondary">Gợi ý:</Typography>
            {suggestions.map((s, i) => (
              <Chip key={i} label={s} variant="outlined" size="small" clickable onClick={() => send(s)} />
            ))}
          </Stack>
        )}

        <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
          <TextField
            fullWidth
            placeholder="Nhập câu hỏi..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send()
              }
            }}
            disabled={loading}
            size="small"
          />
          <Button
            variant="contained"
            endIcon={<SendIcon />}
            onClick={() => send()}
            disabled={loading || !input.trim()}
          >
            Gửi
          </Button>
        </Stack>
      </Stack>
    </Box>
  )
}
