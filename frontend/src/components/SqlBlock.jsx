import { useState } from 'react'
import { Box, Button, Chip, Collapse, Paper, Stack, Typography } from '@mui/material'
import CodeIcon from '@mui/icons-material/Code'

// Hiển thị câu SQL sinh ra (có thể thu gọn) + trạng thái guardrail.
export default function SqlBlock({ sql, validation, executionTime }) {
  const [open, setOpen] = useState(false)
  if (!sql) return null

  const safe = validation?.safe
  return (
    <Box sx={{ mt: 1 }}>
      <Stack direction="row" spacing={1} alignItems="center">
        <Button
          size="small"
          startIcon={<CodeIcon />}
          onClick={() => setOpen((v) => !v)}
          variant="text"
        >
          {open ? 'Ẩn SQL' : 'Xem SQL'}
        </Button>
        {validation && (
          <Chip
            size="small"
            label={safe ? 'Guardrail: An toàn' : 'Guardrail: Đã chặn'}
            color={safe ? 'success' : 'error'}
            variant="outlined"
          />
        )}
        {executionTime != null && (
          <Typography variant="caption" color="text.secondary">
            Thực thi: {executionTime} ms
          </Typography>
        )}
      </Stack>
      <Collapse in={open}>
        <Paper
          variant="outlined"
          sx={{
            mt: 1,
            p: 1.5,
            bgcolor: '#0f172a',
            color: '#e2e8f0',
            fontFamily: 'monospace',
            fontSize: 13,
            whiteSpace: 'pre-wrap',
            overflowX: 'auto',
          }}
        >
          {sql}
        </Paper>
        {validation && !safe && (
          <Typography variant="caption" color="error">
            {validation.reason}
          </Typography>
        )}
      </Collapse>
    </Box>
  )
}
