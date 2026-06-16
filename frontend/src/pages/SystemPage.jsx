import { useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Grid,
  Snackbar,
  Stack,
  Typography,
} from '@mui/material'
import StorageIcon from '@mui/icons-material/Storage'
import HubIcon from '@mui/icons-material/Hub'
import PsychologyIcon from '@mui/icons-material/Psychology'
import RefreshIcon from '@mui/icons-material/Refresh'
import BuildIcon from '@mui/icons-material/Build'
import StatusCard from '../components/StatusCard'
import StatsPanel from '../components/StatsPanel'
import useSystemStatus from '../hooks/useSystemStatus'
import api from '../services/api'

export default function SystemPage() {
  const { status, error, loading, refresh } = useSystemStatus(10000)
  const [busy, setBusy] = useState(false)
  const [toast, setToast] = useState(null)

  async function runAction(label, fn) {
    setBusy(true)
    try {
      const data = await fn()
      setToast(`${label}: thành công (${JSON.stringify(data).slice(0, 120)})`)
      refresh()
    } catch (e) {
      setToast(`${label}: lỗi - ${e.message}`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">Trạng thái hệ thống (tự cập nhật mỗi 10s)</Typography>
        <Button startIcon={<RefreshIcon />} onClick={refresh} disabled={loading}>
          Làm mới
        </Button>
      </Stack>

      {error && <Alert severity="warning" sx={{ mb: 2 }}>Không lấy được trạng thái: {error}</Alert>}

      <Grid container spacing={2}>
        <Grid item xs={12} md={4}>
          <StatusCard title="MySQL DataMart" icon={<StorageIcon color="primary" />} component={status?.mysql} />
        </Grid>
        <Grid item xs={12} md={4}>
          <StatusCard title="Vector DB" icon={<HubIcon color="primary" />} component={status?.vector_db} />
        </Grid>
        <Grid item xs={12} md={4}>
          <StatusCard title="LLM" icon={<PsychologyIcon color="primary" />} component={status?.llm} />
        </Grid>
      </Grid>

      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Quản trị RAG
        </Typography>
        <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
          <Button
            variant="outlined"
            startIcon={<BuildIcon />}
            disabled={busy}
            onClick={() => runAction('Rebuild Vector DB', api.rebuildVectorDb)}
          >
            Dựng lại Vector DB
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            disabled={busy}
            onClick={() => runAction('Reload Metadata', api.reloadMetadata)}
          >
            Nạp lại Metadata
          </Button>
          <Button
            variant="outlined"
            startIcon={<PsychologyIcon />}
            disabled={busy}
            onClick={() => runAction('LLM Test', () => api.llmTest('Xin chào, bạn là ai?'))}
          >
            Kiểm tra LLM
          </Button>
        </Stack>
      </Box>

      <Box sx={{ mt: 4 }}>
        <StatsPanel />
      </Box>

      <Snackbar
        open={!!toast}
        autoHideDuration={6000}
        onClose={() => setToast(null)}
        message={toast}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      />
    </Box>
  )
}
