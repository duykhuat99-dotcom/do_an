import { useEffect, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Grid,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import QueryStatsIcon from '@mui/icons-material/QueryStats'
import PlotlyChart from '../components/PlotlyChart'
import InsightCard from '../components/InsightCard'
import SqlBlock from '../components/SqlBlock'
import DataTable from '../components/DataTable'
import ConversationSidebar from '../components/ConversationSidebar'
import api from '../services/api'

const STORAGE_KEY = 'analytics_history'
const MAX_ITEMS = 30

// Đọc/ghi lịch sử phân tích trong localStorage (khôi phục đầy đủ biểu đồ + bảng).
function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}
function saveHistory(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, MAX_ITEMS)))
}
function newId() {
  return `an-${Date.now().toString(16)}-${Math.random().toString(16).slice(2, 8)}`
}

export default function DashboardPage() {
  const [history, setHistory] = useState(loadHistory)
  const [activeId, setActiveId] = useState(null)
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    saveHistory(history)
  }, [history])

  async function run() {
    const q = question.trim()
    if (!q || loading) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await api.chart({ question: q })
      setResult(data)
      if (data.error) {
        setError(data.error)
      } else {
        // Lưu đầy đủ kết quả để khôi phục nguyên vẹn về sau.
        const item = { id: newId(), question: q, createdAt: new Date().toISOString(), result: data }
        setHistory((h) => [item, ...h].slice(0, MAX_ITEMS))
        setActiveId(item.id)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function newAnalysis() {
    setActiveId(null)
    setQuestion('')
    setResult(null)
    setError(null)
  }

  function selectItem(id) {
    const item = history.find((h) => h.id === id)
    if (!item) return
    setActiveId(id)
    setQuestion(item.question)
    setResult(item.result)
    setError(null)
  }

  // Map sang định dạng sidebar dùng chung.
  const sidebarItems = history.map((h) => ({
    session_id: h.id,
    title: h.question,
    last_at: h.createdAt,
  }))

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 160px)' }}>
      <ConversationSidebar
        sessions={sidebarItems}
        activeId={activeId}
        onSelect={selectItem}
        onNew={newAnalysis}
        loading={false}
        newLabel="Phân tích mới"
        emptyText="Chưa có phân tích nào."
      />

      <Box sx={{ flex: 1, pl: 2, minWidth: 0, overflowY: 'auto' }}>
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <TextField
            fullWidth
            size="small"
            label="Câu hỏi phân tích"
            placeholder="Ví dụ: Doanh thu theo danh mục sản phẩm?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && run()}
          />
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <QueryStatsIcon />}
            onClick={run}
            disabled={loading || !question.trim()}
          >
            Phân tích
          </Button>
        </Stack>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        {result && !result.error && (
          <Grid container spacing={2}>
            <Grid item xs={12} md={7}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Biểu đồ
                  </Typography>
                  {result.chart ? (
                    <PlotlyChart chart={result.chart} />
                  ) : (
                    <Typography color="text.secondary">Không có biểu đồ phù hợp.</Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={5}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Phân tích
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {result.question}
                  </Typography>
                  <SqlBlock sql={result.sql} />
                  {result.insight && <InsightCard insight={result.insight} />}
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Dữ liệu ({result.row_count ?? 0} dòng)
                  </Typography>
                  <DataTable columns={result.columns} rows={result.rows} />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {!result && !loading && !error && (
          <Box sx={{ textAlign: 'center', mt: 6, color: 'text.secondary' }}>
            <Typography variant="h6">Nhập câu hỏi để phân tích 📊</Typography>
            <Typography variant="body2">
              Mỗi lần phân tích sẽ được lưu vào danh sách bên trái để xem lại.
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  )
}
