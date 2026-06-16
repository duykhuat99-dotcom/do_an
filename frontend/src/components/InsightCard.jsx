import { Alert, Box, Chip, Stack, Typography } from '@mui/material'
import InsightsIcon from '@mui/icons-material/Insights'

// Hiển thị AI Insight (nhận định) + các điểm nổi bật.
export default function InsightCard({ insight }) {
  if (!insight) return null
  return (
    <Alert
      icon={<InsightsIcon fontSize="inherit" />}
      severity="info"
      sx={{ mt: 1, '& .MuiAlert-message': { width: '100%' } }}
    >
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 0.5 }}>
        <Typography variant="subtitle2">AI Insight</Typography>
        <Chip
          size="small"
          label={insight.llm_used ? 'LLM' : 'Theo quy tắc'}
          variant="outlined"
        />
      </Stack>
      <Typography variant="body2">{insight.summary}</Typography>
      {insight.highlights?.length > 0 && (
        <Box component="ul" sx={{ mt: 0.5, mb: 0, pl: 2 }}>
          {insight.highlights.map((h, i) => (
            <li key={i}>
              <Typography variant="caption">{h}</Typography>
            </li>
          ))}
        </Box>
      )}
    </Alert>
  )
}
