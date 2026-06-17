import { useState } from 'react'
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Menu,
  MenuItem,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline'
import MoreVertIcon from '@mui/icons-material/MoreVert'
import EditIcon from '@mui/icons-material/Edit'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'

// Sidebar liệt kê các mục lịch sử + nút tạo mới + đổi tên/xóa.
// Mỗi item dạng { session_id, title, last_at }.
export default function ConversationSidebar({
  sessions,
  activeId,
  onSelect,
  onNew,
  loading,
  onRename,
  onDelete,
  newLabel = 'Cuộc trò chuyện mới',
  emptyText = 'Chưa có cuộc trò chuyện nào.',
}) {
  const [menuAnchor, setMenuAnchor] = useState(null)
  const [target, setTarget] = useState(null) // session đang thao tác
  const [renameOpen, setRenameOpen] = useState(false)
  const [renameValue, setRenameValue] = useState('')

  const hasMenu = !!(onRename || onDelete)

  function openMenu(e, s) {
    e.stopPropagation()
    setMenuAnchor(e.currentTarget)
    setTarget(s)
  }
  function closeMenu() {
    setMenuAnchor(null)
  }
  function startRename() {
    setRenameValue(target?.title || '')
    setRenameOpen(true)
    closeMenu()
  }
  function confirmRename() {
    const v = renameValue.trim()
    if (v && target) onRename?.(target.session_id, v)
    setRenameOpen(false)
  }
  function confirmDelete() {
    if (target && window.confirm(`Xóa "${target.title}"? Hành động này không hoàn tác được.`)) {
      onDelete?.(target.session_id)
    }
    closeMenu()
  }

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
          <ListItem
            key={s.session_id}
            disablePadding
            secondaryAction={
              hasMenu ? (
                <IconButton edge="end" size="small" onClick={(e) => openMenu(e, s)}>
                  <MoreVertIcon fontSize="small" />
                </IconButton>
              ) : undefined
            }
          >
            <ListItemButton
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
          </ListItem>
        ))}
      </List>

      {/* Menu đổi tên / xóa */}
      <Menu anchorEl={menuAnchor} open={!!menuAnchor} onClose={closeMenu}>
        {onRename && (
          <MenuItem onClick={startRename}>
            <EditIcon fontSize="small" sx={{ mr: 1 }} /> Đổi tên
          </MenuItem>
        )}
        {onDelete && (
          <MenuItem onClick={confirmDelete} sx={{ color: 'error.main' }}>
            <DeleteOutlineIcon fontSize="small" sx={{ mr: 1 }} /> Xóa
          </MenuItem>
        )}
      </Menu>

      {/* Hộp thoại đổi tên */}
      <Dialog open={renameOpen} onClose={() => setRenameOpen(false)} fullWidth maxWidth="xs">
        <DialogTitle>Đổi tên cuộc trò chuyện</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            size="small"
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && confirmRename()}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRenameOpen(false)}>Hủy</Button>
          <Button variant="contained" onClick={confirmRename} disabled={!renameValue.trim()}>
            Lưu
          </Button>
        </DialogActions>
      </Dialog>
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
