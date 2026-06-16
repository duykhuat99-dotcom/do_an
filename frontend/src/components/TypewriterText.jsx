import { useEffect, useRef, useState } from 'react'
import { Typography } from '@mui/material'

// Hiệu ứng "gõ chữ" (typing) cho cảm giác streaming như ChatGPT.
export default function TypewriterText({ text, speed = 14, charsPerTick = 2, variant = 'body1' }) {
  const [shown, setShown] = useState('')
  const timer = useRef(null)

  useEffect(() => {
    setShown('')
    if (!text) return
    let i = 0
    timer.current = setInterval(() => {
      i += charsPerTick
      setShown(text.slice(0, i))
      if (i >= text.length) clearInterval(timer.current)
    }, speed)
    return () => clearInterval(timer.current)
  }, [text, speed, charsPerTick])

  return (
    <Typography variant={variant} sx={{ whiteSpace: 'pre-wrap' }}>
      {shown}
    </Typography>
  )
}
