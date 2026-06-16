import Plot from 'react-plotly.js'
import { Box, Typography } from '@mui/material'

// Render cấu hình Plotly JSON {data, layout} nhận từ backend.
export default function PlotlyChart({ chart }) {
  if (!chart || !chart.plotly) return null
  const { data, layout } = chart.plotly
  return (
    <Box sx={{ width: '100%' }}>
      {chart.title && (
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          {chart.chart_type?.toUpperCase()} · {chart.reason}
        </Typography>
      )}
      <Plot
        data={data}
        layout={{ ...layout, autosize: true, margin: { t: 40, r: 20, b: 50, l: 60 } }}
        useResizeHandler
        style={{ width: '100%', height: '380px' }}
        config={{
          responsive: true,
          displaylogo: false,
          displayModeBar: true,
          // Chỉ giữ nút tải ảnh PNG, bỏ các nút zoom/pan cho gọn.
          modeBarButtonsToRemove: [
            'lasso2d', 'select2d', 'zoom2d', 'pan2d',
            'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d',
          ],
          toImageButtonOptions: { format: 'png', filename: 'bieu_do', scale: 2 },
        }}
      />
    </Box>
  )
}
