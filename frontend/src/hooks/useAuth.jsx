import { createContext, useContext, useEffect, useState } from 'react'
import api, { TOKEN_KEY } from '../services/api'

const USER_KEY = 'auth_user'
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [username, setUsername] = useState(() => localStorage.getItem(USER_KEY))

  // Khi token hết hạn (interceptor phát sự kiện) -> đăng xuất.
  useEffect(() => {
    const onExpired = () => {
      setToken(null)
      setUsername(null)
    }
    window.addEventListener('auth-expired', onExpired)
    return () => window.removeEventListener('auth-expired', onExpired)
  }, [])

  const login = async (u, p) => {
    const data = await api.login(u, p)
    localStorage.setItem(TOKEN_KEY, data.access_token)
    localStorage.setItem(USER_KEY, data.username)
    setToken(data.access_token)
    setUsername(data.username)
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUsername(null)
  }

  return (
    <AuthContext.Provider value={{ token, username, isAuthed: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
