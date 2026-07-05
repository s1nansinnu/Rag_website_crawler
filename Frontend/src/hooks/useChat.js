import { useState, useCallback } from 'react'

export function useChat() {
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState(null)

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
    setIsStreaming(false)
  }, [])

  const sendMessage = useCallback(async (question, sessionId) => {
    if (!question.trim() || !sessionId) return

    setError(null)
    setIsStreaming(true)

    // Add user message
    const userMsg = { role: 'user', content: question }
    setMessages(prev => [...prev, userMsg])

    // Prepare placeholder for bot message
    const botMsgPlaceholder = { role: 'bot', content: '', sources: [] }
    setMessages(prev => [...prev, botMsgPlaceholder])

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question, session_id: sessionId }),
      })

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentEvent = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) continue

          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.slice(6).trim()
          } else if (trimmed.startsWith('data:')) {
            const dataStr = trimmed.slice(5).trim()
            try {
              const data = JSON.parse(dataStr)

              if (currentEvent === 'token') {
                setMessages(prev => {
                  const updated = [...prev]
                  const last = updated[updated.length - 1]
                  if (last && last.role === 'bot') {
                    last.content += data.text
                  }
                  return updated
                })
              } else if (currentEvent === 'sources') {
                setMessages(prev => {
                  const updated = [...prev]
                  const last = updated[updated.length - 1]
                  if (last && last.role === 'bot') {
                    last.sources = data.urls || []
                  }
                  return updated
                })
              } else if (currentEvent === 'error') {
                setError(data.message || 'An error occurred during response generation.')
                setIsStreaming(false)
              } else if (currentEvent === 'done') {
                setIsStreaming(false)
              }
            } catch (err) {
              console.error('Failed to parse chat SSE event:', err)
            }
          }
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to establish connection for streaming.')
      setIsStreaming(false)
      // Remove the blank bot message placeholder if we failed immediately
      setMessages(prev => {
        const updated = [...prev]
        if (updated.length > 0 && updated[updated.length - 1].content === '') {
          updated.pop()
        }
        return updated
      })
    }
  }, [])

  return {
    messages,
    isStreaming,
    error,
    sendMessage,
    clearMessages,
  }
}
