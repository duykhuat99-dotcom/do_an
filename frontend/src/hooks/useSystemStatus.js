import { useCallback, useEffect, useRef, useState } from 'react'
import api from '../services/api'

// Hook poll trạng thái hệ thống (MySQL / Vector DB / LLM) theo chu kỳ.
export default function useSystemStatus(intervalMs = 10000) {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const timer = useRef(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.systemStatus()
      setStatus(data)
      setError(null)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    if (intervalMs > 0) {
      timer.current = setInterval(refresh, intervalMs)
      return () => clearInterval(timer.current)
    }
  }, [refresh, intervalMs])

  return { status, error, loading, refresh }
}
