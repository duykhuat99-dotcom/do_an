import { useEffect, useRef, useState } from 'react'
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
import QueryStatsIcon from '@mui/icons-material/QueryStats'
import AnalysisResult from '../components/AnalysisResult'
import ConversationSidebar from '../components/ConversationSidebar'
import api from '../services/api'

const STORAGE_KEY = 'analytics_sessions'
const OLD_KEY = 'analytics_history'
const MAX_SESSIONS = 30

// Mỗi session = một khung phân tích gồm nhiều lượt (turns).
function loadSessions() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
    // Di trú từ định dạng cũ (mỗi phân tích là 1 mục phẳng) -> mỗi mục thành 1 session 1 lượt.
    const old = JSON.parse(localStorage.getItem(OLD_KEY) || '[]')
    return old.map((o) => ({
      id: o.id,
      title: o.title || o.question,
      createdAt: o.createdAt,
      turns: [{ question: o.question, result: o.result }],
    }))
  } catch {
    return []
  }
}
function newId() {
  return `an-${Date.now().toString(16)}-${Math.random().toString(16).slice(2, 8)}`
}

const SUGGESTIONS = [
  'Doanh thu theo chi nhánh năm 2024?',
  'Top 5 sản phẩm bán chạy nhất?',
  'Cơ cấu doanh thu theo danh mục?',
]

export default function DashboardPage() {
  const [sessions, setSessions] = useState(loadSessions)
  const [activeId, setActiveId] = useState(null)
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, MAX_SESSIONS)))
  }, [sessions])

  const active = sessions.find((s) => s.id === activeId)
  const turns = active?.turns || []

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [turns.length, loading])

  async function run(q) {
    const text = (q ?? question).trim()
    if (!text || loading) return
    setQuestion('')
    setLoading(true)

    let sid = activeId
    const isNew = !sid
    // Lịch sử các lượt trước trong khung -> giúp hiểu câu hỏi nối tiếp.
    const history = (active?.turns || []).map((t) => ({
      question: t.question,
      sql: t.result?.sql || null,
    }))
    if (isNew) {
      sid = newId()
      setSessions((prev) =>
        [{ id: sid, title: text, createdAt: new Date().toISOString(), turns: [] }, ...prev].slice(
          0,
          MAX_SESSIONS
        )
      )
      setActiveId(sid)
    }

    try {
      const data = await api.chart({ question: text, history })
      const turn = { question: text, result: data }
      setSessions((prev) =>
        prev.map((s) =>
          s.id === sid
            ? { ...s, turns: [...s.turns, turn], createdAt: new Date().toISOString() }
            : s
        )
      )
    } catch (e) {
      const turn = { question: text, result: { error: e.message } }
      setSessions((prev) =>
        prev.map((s) => (s.id === sid ? { ...s, turns: [...s.turns, turn] } : s))
      )
    } finally {
      setLoading(false)
    }
  }

  function newAnalysis() {
    setActiveId(null)
    setQuestion('')
  }
  function selectItem(id) {
    setActiveId(id)
    setQuestion('')
  }
  function renameItem(id, title) {
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title } : s)))
  }
  function deleteItem(id) {
    setSessions((prev) => prev.filter((s) => s.id !== id))
    if (id === activeId) newAnalysis()
  }

  const sidebarItems = sessions.map((s) => ({
    session_id: s.id,
    title: s.title,
    last_at: s.createdAt,
  }))

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 160px)' }}>
      <ConversationSidebar
        sessions={sidebarItems}
        activeId={activeId}
        onSelect={selectItem}
        onNew={newAnalysis}
        loading={false}
        onRename={renameItem}
        onDelete={deleteItem}
        newLabel="Phân tích mới"
        emptyText="Chưa có phân tích nào."
      />

      <Stack sx={{ flex: 1, pl: 2, minWidth: 0 }}>
        <Paper variant="outlined" sx={{ flex: 1, p: 2, overflowY: 'auto', bgcolor: 'grey.50' }}>
          {turns.length === 0 && !loading && (
            <Box sx={{ textAlign: 'center', mt: 6 }}>
              <Typography variant="h6" gutterBottom>
                Phân tích dữ liệu bằng câu hỏi 📊
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Hỏi nhiều câu liên tục trong cùng một khung — mỗi câu cho ra biểu đồ + phân tích.
              </Typography>
              <Stack direction="row" spacing={1} justifyContent="center" flexWrap="wrap" useFlexGap>
                {SUGGESTIONS.map((s) => (
                  <Button key={s} size="small" variant="outlined" onClick={() => run(s)}>
                    {s}
                  </Button>
                ))}
              </Stack>
            </Box>
          )}

          {turns.map((t, i) => (
            <Box key={i} sx={{ mb: 3 }}>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <Chip label={`Câu ${i + 1}`} size="small" color="primary" />
                <Typography variant="subtitle1" fontWeight={600}>
                  {t.question}
                </Typography>
              </Stack>
              <AnalysisResult result={t.result} />
            </Box>
          ))}

          {loading && (
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1 }}>
              <CircularProgress size={18} />
              <Typography variant="body2" color="text.secondary">
                Đang phân tích...
              </Typography>
            </Stack>
          )}
          <div ref={endRef} />
        </Paper>

        <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Nhập câu hỏi phân tích..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                run()
              }
            }}
            disabled={loading}
          />
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <QueryStatsIcon />}
            onClick={() => run()}
            disabled={loading || !question.trim()}
          >
            Phân tích
          </Button>
        </Stack>
      </Stack>
    </Box>
  )
}
