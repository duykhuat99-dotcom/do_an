import { useCallback, useEffect, useState } from 'react'
import {
  Box,
  Button,
  Card,
  CardContent,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import Plot from 'react-plotly.js'
import api from '../services/api'

function StatCard({ label, value, color }) {
  return (
    <Card variant="outlined" sx={{ textAlign: 'center' }}>
      <CardContent>
        <Typography variant="h4" color={color || 'primary'}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
      </CardContent>
    </Card>
  )
}

export default function StatsPanel() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setStats(await api.stats())
    } catch {
      /* DB chưa sẵn sàng */
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const byDay = stats?.by_day || []

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">Thống kê truy vấn</Typography>
        <Button startIcon={<RefreshIcon />} onClick={load} disabled={loading}>
          Làm mới
        </Button>
      </Stack>

      <Grid container spacing={2}>
        <Grid item xs={6} md={3}>
          <StatCard label="Tổng truy vấn" value={stats?.total_queries ?? 0} />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard label="Tỷ lệ thành công" value={`${stats?.success_rate ?? 0}%`} color="success.main" />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard label="Thời gian TB (ms)" value={stats?.avg_execution_ms ?? 0} />
        </Grid>
        <Grid item xs={6} md={3}>
          <StatCard label="Đánh giá 👍 / 👎" value={`${stats?.feedback_up ?? 0} / ${stats?.feedback_down ?? 0}`} />
        </Grid>
      </Grid>

      <Grid container spacing={2} sx={{ mt: 0.5 }}>
        <Grid item xs={12} md={7}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Truy vấn theo ngày
              </Typography>
              {byDay.length > 0 ? (
                <Plot
                  data={[
                    { type: 'bar', name: 'Tổng', x: byDay.map((d) => d.date), y: byDay.map((d) => d.total) },
                    { type: 'bar', name: 'Thành công', x: byDay.map((d) => d.date), y: byDay.map((d) => d.success) },
                  ]}
                  layout={{ barmode: 'group', autosize: true, margin: { t: 10, r: 10, b: 40, l: 40 }, legend: { orientation: 'h' } }}
                  useResizeHandler
                  style={{ width: '100%', height: '280px' }}
                  config={{ displayModeBar: false, responsive: true }}
                />
              ) : (
                <Typography color="text.secondary">Chưa có dữ liệu.</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={5}>
          <Card variant="outlined" sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Câu hỏi phổ biến
              </Typography>
              <Divider />
              <List dense>
                {(stats?.top_questions || []).map((t, i) => (
                  <ListItem key={i} disableGutters>
                    <ListItemText
                      primary={t.question || '(trống)'}
                      secondary={`${t.count} lần`}
                      primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                    />
                  </ListItem>
                ))}
                {(stats?.top_questions || []).length === 0 && (
                  <Typography color="text.secondary" variant="body2" sx={{ mt: 1 }}>
                    Chưa có dữ liệu.
                  </Typography>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
