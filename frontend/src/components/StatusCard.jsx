import { Card, CardContent, Chip, Stack, Typography, Box } from '@mui/material'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorIcon from '@mui/icons-material/Error'

// Thẻ trạng thái một thành phần hạ tầng (MySQL / Vector DB / LLM).
export default function StatusCard({ title, icon, component }) {
  const healthy = component?.healthy
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Stack direction="row" alignItems="center" spacing={1}>
            {icon}
            <Typography variant="h6">{title}</Typography>
          </Stack>
          <Chip
            icon={healthy ? <CheckCircleIcon /> : <ErrorIcon />}
            label={healthy ? 'Hoạt động' : 'Lỗi'}
            color={healthy ? 'success' : 'error'}
            size="small"
          />
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {component?.detail || '—'}
        </Typography>
        {component?.info && Object.keys(component.info).length > 0 && (
          <Box sx={{ mt: 1 }}>
            {Object.entries(component.info).map(([k, v]) => (
              <Typography key={k} variant="caption" display="block" color="text.secondary">
                {k}: {String(v)}
              </Typography>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  )
}
