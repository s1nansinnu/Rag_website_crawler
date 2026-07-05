import { useState, useCallback } from 'react'

export function useCrawl() {
  const [phase, setPhase] = useState('idle') // 'idle', 'crawling', 'chunking', 'embedding', 'complete', 'error'
  const [progress, setProgress] = useState({ pages_crawled: 0, total_discovered: 0, current_url: '' })
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [totalChunks, setTotalChunks] = useState(0)

  const resetCrawl = useCallback(() => {
    setPhase('idle')
    setProgress({ pages_crawled: 0, total_discovered: 0, current_url: '' })
    setError(null)
    setSessionId(null)
    setTotalChunks(0)
  }, [])

  const startCrawl = useCallback(async (url, maxPages = 10) => {
    setPhase('crawling')
    setProgress({ pages_crawled: 0, total_discovered: 0, current_url: url })
    setError(null)
    setTotalChunks(0)

    try {
      const response = await fetch('/api/crawl', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, max_pages: maxPages }),
      })

      if (!response.ok) {
        throw new Error(`Failed to start crawl: ${response.statusText}`)
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

              if (data.session_id) {
                setSessionId(data.session_id)
              }

              if (currentEvent === 'progress') {
                setProgress({
                  pages_crawled: data.pages_crawled,
                  total_discovered: data.total_discovered,
                  current_url: data.current_url || ''
                })
                setPhase('crawling')
              } else if (currentEvent === 'chunking') {
                setPhase('chunking')
              } else if (currentEvent === 'embedding') {
                setPhase('embedding')
              } else if (currentEvent === 'complete') {
                // Capture real chunk count from backend complete event
                setTotalChunks(data.total_chunks || 0)
                setPhase('complete')
              } else if (currentEvent === 'error') {
                setPhase('error')
                setError(data.message || 'An error occurred during crawling.')
              }
            } catch (err) {
              console.error('Failed to parse SSE event data:', err)
            }
          }
        }
      }
    } catch (err) {
      setPhase('error')
      setError(err.message || 'Failed to establish connection to server.')
    }
  }, [])

  return {
    startCrawl,
    resetCrawl,
    phase,
    progress,
    error,
    sessionId,
    totalChunks,
    isComplete: phase === 'complete'
  }
}