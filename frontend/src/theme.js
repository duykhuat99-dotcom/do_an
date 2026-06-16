import { createTheme } from '@mui/material/styles'

const theme = createTheme({
  palette: {
    primary: { main: '#1565c0', 50: '#e3f2fd', 200: '#90caf9' },
    secondary: { main: '#7b1fa2' },
    background: { default: '#f4f6f8' },
  },
  shape: { borderRadius: 10 },
  typography: {
    fontFamily: 'Roboto, "Segoe UI", Arial, sans-serif',
  },
})

export default theme
