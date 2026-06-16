import {
  Button,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import DownloadIcon from '@mui/icons-material/Download'

// Bảng dữ liệu kết quả truy vấn (giới hạn số dòng hiển thị cho gọn).
export default function DataTable({ columns, rows, maxRows = 50 }) {
  if (!columns?.length || !rows?.length) return null
  const shown = rows.slice(0, maxRows)

  return (
    <>
      <Stack direction="row" justifyContent="flex-end" sx={{ mb: 0.5 }}>
        <Button
          size="small"
          startIcon={<DownloadIcon />}
          onClick={() => exportCsv(columns, rows)}
        >
          Tải CSV ({rows.length} dòng)
        </Button>
      </Stack>
      <TableContainer component={Paper} variant="outlined" sx={{ mt: 1, maxHeight: 360 }}>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              {columns.map((c) => (
                <TableCell key={c} sx={{ fontWeight: 600 }}>
                  {c}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {shown.map((row, i) => (
              <TableRow key={i} hover>
                {columns.map((c) => (
                  <TableCell key={c}>{formatCell(row[c])}</TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      {rows.length > maxRows && (
        <Typography variant="caption" color="text.secondary">
          Hiển thị {maxRows}/{rows.length} dòng.
        </Typography>
      )}
    </>
  )
}

function formatCell(v) {
  if (v == null) return '—'
  if (typeof v === 'number') return v.toLocaleString('vi-VN')
  return String(v)
}

// Xuất toàn bộ dữ liệu ra file CSV (UTF-8 BOM để Excel đọc đúng tiếng Việt).
function exportCsv(columns, rows) {
  const esc = (v) => {
    if (v == null) return ''
    const s = String(v)
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const head = columns.join(',')
  const body = rows.map((r) => columns.map((c) => esc(r[c])).join(',')).join('\n')
  const blob = new Blob(['﻿' + head + '\n' + body], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'du_lieu.csv'
  a.click()
  URL.revokeObjectURL(url)
}
