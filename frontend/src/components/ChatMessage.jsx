import { useState } from 'react'
import { Box, Chip, CircularProgress, IconButton, Paper, Stack, Tooltip, Typography } from '@mui/material'
import PersonIcon from '@mui/icons-material/Person'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline'
import ThumbUpAltOutlinedIcon from '@mui/icons-material/ThumbUpAltOutlined'
import ThumbDownAltOutlinedIcon from '@mui/icons-material/ThumbDownAltOutlined'
import SqlBlock from './SqlBlock'
import InsightCard from './InsightCard'
import PlotlyChart from './PlotlyChart'
import TypewriterText from './TypewriterText'

// Một bong bóng hội thoại. role: 'user' | 'assistant'.
export default function ChatMessage({ role, content, data, loading, animate, onFeedback }) {
  const isUser = role === 'user'
  const [rated, setRated] = useState(null)

  function rate(r) {
    if (rated) return
    setRated(r)
    onFeedback?.(r)
  }
  return (
    <Stack
      direction="row"
      spacing={1.5}
      sx={{ mb: 2, flexDirection: isUser ? 'row-reverse' : 'row' }}
    >
      <Box
        sx={{
          width: 36,
          height: 36,
          borderRadius: '50%',
          bgcolor: isUser ? 'primary.main' : 'secondary.main',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {isUser ? <PersonIcon /> : <SmartToyIcon />}
      </Box>
      <Paper
        variant="outlined"
        sx={{
          p: 1.5,
          maxWidth: '80%',
          bgcolor: isUser ? 'primary.50' : 'background.paper',
          borderColor: isUser ? 'primary.200' : 'divider',
        }}
      >
        {!isUser && data?.mode === 'general' && (
          <Chip
            size="small"
            icon={<ChatBubbleOutlineIcon />}
            label="Trò chuyện"
            variant="outlined"
            sx={{ mb: 1 }}
          />
        )}

        {loading ? (
          <Stack direction="row" spacing={1} alignItems="center">
            <CircularProgress size={16} />
            <Typography variant="body2" color="text.secondary">
              Đang phân tích...
            </Typography>
          </Stack>
        ) : animate && !isUser ? (
          <TypewriterText text={content} />
        ) : (
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {content}
          </Typography>
        )}

        {/* Khối SQL/biểu đồ/insight chỉ hiện cho câu phân tích dữ liệu (mode != general) */}
        {data && !isUser && data.mode !== 'general' && (
          <Box sx={{ mt: 1 }}>
            <SqlBlock
              sql={data.sql}
              validation={data.validation}
              executionTime={data.execution_time_ms}
            />
            {data.insight && <InsightCard insight={data.insight} />}
            {data.chart && (
              <Box sx={{ mt: 1 }}>
                <PlotlyChart chart={data.chart} />
              </Box>
            )}
            {data.total_time_ms != null && (
              <Typography variant="caption" color="text.secondary">
                Tổng thời gian: {data.total_time_ms} ms
              </Typography>
            )}
          </Box>
        )}

        {/* Nút đánh giá 👍/👎 cho câu trả lời */}
        {onFeedback && !isUser && !loading && (
          <Stack direction="row" spacing={0.5} alignItems="center" sx={{ mt: 0.5 }}>
            <Tooltip title="Hữu ích">
              <IconButton size="small" color={rated === 'up' ? 'success' : 'default'} onClick={() => rate('up')}>
                <ThumbUpAltOutlinedIcon fontSize="inherit" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Chưa tốt">
              <IconButton size="small" color={rated === 'down' ? 'error' : 'default'} onClick={() => rate('down')}>
                <ThumbDownAltOutlinedIcon fontSize="inherit" />
              </IconButton>
            </Tooltip>
            {rated && <Typography variant="caption" color="text.secondary">Cảm ơn đánh giá!</Typography>}
          </Stack>
        )}
      </Paper>
    </Stack>
  )
}
