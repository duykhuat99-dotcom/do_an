import { useState } from 'react'
import {
  AppBar,
  Box,
  Button,
  Container,
  Stack,
  Tab,
  Tabs,
  Toolbar,
  Typography,
} from '@mui/material'
import ChatIcon from '@mui/icons-material/Chat'
import DashboardIcon from '@mui/icons-material/Dashboard'
import SettingsIcon from '@mui/icons-material/Settings'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import LogoutIcon from '@mui/icons-material/Logout'
import PersonIcon from '@mui/icons-material/Person'
import ChatPage from './pages/ChatPage'
import DashboardPage from './pages/DashboardPage'
import SystemPage from './pages/SystemPage'
import LoginPage from './pages/LoginPage'
import { useAuth } from './hooks/useAuth'

export default function App() {
  const [tab, setTab] = useState(0)
  const { isAuthed, username, logout } = useAuth()

  if (!isAuthed) return <LoginPage />

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <SmartToyIcon sx={{ mr: 1.5 }} />
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Chatbot AI Phân tích DataMart (RAG + LLM)
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center">
            <PersonIcon fontSize="small" />
            <Typography variant="body2">{username}</Typography>
            <Button color="inherit" size="small" startIcon={<LogoutIcon />} onClick={logout}>
              Đăng xuất
            </Button>
          </Stack>
        </Toolbar>
        <Tabs
          value={tab}
          onChange={(_, v) => setTab(v)}
          textColor="inherit"
          indicatorColor="secondary"
          variant="fullWidth"
        >
          <Tab icon={<ChatIcon />} iconPosition="start" label="Chat Assistant" />
          <Tab icon={<DashboardIcon />} iconPosition="start" label="Analytics Dashboard" />
          <Tab icon={<SettingsIcon />} iconPosition="start" label="System Management" />
        </Tabs>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 3 }}>
        {tab === 0 && <ChatPage />}
        {tab === 1 && <DashboardPage />}
        {tab === 2 && <SystemPage />}
      </Container>
    </Box>
  )
}
