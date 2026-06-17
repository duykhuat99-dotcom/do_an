import axios from 'axios'

// Ưu tiên biến môi trường; mặc định gọi thẳng backend FastAPI.
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL,
  timeout: 180000, // LLM có thể chạy lâu
  headers: { 'Content-Type': 'application/json' },
})

export const TOKEN_KEY = 'auth_token'

// Đính token vào mọi request nếu đã đăng nhập.
client.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Token hết hạn/không hợp lệ -> xoá token và báo cho app để quay về Login.
client.interceptors.response.use(
  (resp) => resp,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      window.dispatchEvent(new Event('auth-expired'))
    }
    return Promise.reject(err)
  }
)

// Gom thông điệp lỗi về một chỗ cho dễ hiển thị.
function toError(err) {
  const detail =
    err?.response?.data?.error ||
    err?.response?.data?.detail ||
    err?.message ||
    'Lỗi không xác định'
  return new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
}

export const api = {
  // ----- Xác thực -----
  async login(username, password) {
    try {
      const { data } = await client.post('/auth/login', { username, password })
      return data
    } catch (e) {
      throw toError(e)
    }
  },

  // ----- Hội thoại -----
  async chat(payload) {
    try {
      const { data } = await client.post('/chat', payload)
      return data
    } catch (e) {
      throw toError(e)
    }
  },
  async generateSql(payload) {
    try {
      const { data } = await client.post('/generate-sql', payload)
      return data
    } catch (e) {
      throw toError(e)
    }
  },
  async chart(payload) {
    try {
      const { data } = await client.post('/chart', payload)
      return data
    } catch (e) {
      throw toError(e)
    }
  },
  async history(sessionId, limit = 100) {
    try {
      const { data } = await client.post('/history', { session_id: sessionId, limit })
      return data
    } catch (e) {
      throw toError(e)
    }
  },
  async listSessions(limit = 50) {
    try {
      const { data } = await client.get('/sessions', { params: { limit } })
      return data
    } catch (e) {
      throw toError(e)
    }
  },
  async suggestQuestions(question, answer) {
    try {
      const { data } = await client.post('/suggest-questions', { question, answer })
      return data
    } catch (e) {
      throw toError(e)
    }
  },
  async renameSession(sessionId, title) {
    try {
      const { data } = await client.patch(`/sessions/${encodeURIComponent(sessionId)}`, { title })
      return data
    } catch (e) {
      throw toError(e)
    }
  },
  async deleteSession(sessionId) {
    try {
      const { data } = await client.delete(`/sessions/${encodeURIComponent(sessionId)}`)
      return data
    } catch (e) {
      throw toError(e)
    }
  },

  async stats() {
    try {
      const { data } = await client.get('/stats')
      return data
    } catch (e) {
      throw toError(e)
    }
  },
  async sendFeedback(payload) {
    try {
      const { data } = await client.post('/feedback', payload)
      return data
    } catch (e) {
      throw toError(e)
    }
  },

  // ----- Hệ thống -----
  async systemStatus() {
    try {
      const { data } = await client.get('/system-status')
      return data
    } catch (e) {
      throw toError(e)
    }
  },
  async llmTest(prompt) {
    try {
      const { data } = await client.post('/llm-test', { prompt })
      return data
    } catch (e) {
      throw toError(e)
    }
  },

  // ----- Quản trị RAG -----
  async rebuildVectorDb() {
    try {
      const { data } = await client.post('/rebuild-vector-db')
      return data
    } catch (e) {
      throw toError(e)
    }
  },
  async reloadMetadata() {
    try {
      const { data } = await client.post('/reload-metadata')
      return data
    } catch (e) {
      throw toError(e)
    }
  },
}

export default api
