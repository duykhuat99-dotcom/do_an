import {
  Box,
  Button,
  Divider,
  List,
  ListItemButton,
  ListItemText,
  Tooltip,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline'

// Sidebar liệt kê các mục lịch sử (cuộc trò chuyện / phân tích) + nút tạo mới.
// Mỗi item dạng { session_id, title, last_at }.
export default function ConversationSidebar({
  sessions,
  activeId,
  onSelect,
  onNew,
  loading,
  newLabel = 'Cuộc trò chuyện mới',
  emptyText = 'Chưa có cuộc trò chuyện nào.',
}) {
  return (
    <Box
      sx={{
        width: 270,
        flexShrink: 0,
        borderRight: '1px solid',
        borderColor: 'divider',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        bgcolor: 'background.paper',
      }}
    >
      <Box sx={{ p: 1 }}>
        <Button fullWidth variant="contained" startIcon={<AddIcon />} onClick={onNew}>
          {newLabel}
        </Button>
      </Box>
      <Divider />
      <Typography variant="caption" color="text.secondary" sx={{ px: 2, pt: 1 }}>
        Lịch sử {loading ? '(đang tải...)' : `(${sessions.length})`}
      </Typography>
      <List dense sx={{ overflowY: 'auto', flex: 1 }}>
        {sessions.length === 0 && (
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="body2" color="text.secondary">
              {emptyText}
            </Typography>
          </Box>
        )}
        {sessions.map((s) => (
          <ListItemButton
            key={s.session_id}
            selected={s.session_id === activeId}
            onClick={() => onSelect(s.session_id)}
            sx={{ alignItems: 'flex-start' }}
          >
            <ChatBubbleOutlineIcon fontSize="small" sx={{ mr: 1, mt: 0.3, color: 'text.secondary' }} />
            <ListItemText
              primary={
                <Tooltip title={s.title} placement="right">
                  <span>{s.title}</span>
                </Tooltip>
              }
              secondary={relTime(s.last_at)}
              primaryTypographyProps={{ noWrap: true, variant: 'body2' }}
              secondaryTypographyProps={{ variant: 'caption' }}
            />
          </ListItemButton>
        ))}
      </List>
    </Box>
  )
}

// Định dạng thời gian tương đối tiếng Việt.
function relTime(iso) {
  if (!iso) return ''
  const then = new Date(iso)
  const diff = (Date.now() - then.getTime()) / 1000
  if (diff < 60) return 'vừa xong'
  if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`
  if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`
  if (diff < 604800) return `${Math.floor(diff / 86400)} ngày trước`
  return then.toLocaleDateString('vi-VN')
}
