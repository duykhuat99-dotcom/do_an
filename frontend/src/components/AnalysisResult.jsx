import { Alert, Card, CardContent, Grid, Typography } from '@mui/material'
import PlotlyChart from './PlotlyChart'
import InsightCard from './InsightCard'
import SqlBlock from './SqlBlock'
import DataTable from './DataTable'

// Hiển thị một kết quả phân tích: biểu đồ + SQL + insight + bảng dữ liệu.
export default function AnalysisResult({ result }) {
  if (!result) return null
  if (result.error) {
    return <Alert severity="warning">{result.error}</Alert>
  }
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={7}>
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
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
            <Typography variant="subtitle1" gutterBottom>
              Phân tích
            </Typography>
            <SqlBlock sql={result.sql} />
            {result.insight && <InsightCard insight={result.insight} />}
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12}>
        <Card variant="outlined">
          <CardContent>
            <Typography variant="subtitle1" gutterBottom>
              Dữ liệu ({result.row_count ?? 0} dòng)
            </Typography>
            <DataTable columns={result.columns} rows={result.rows} />
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  )
}
