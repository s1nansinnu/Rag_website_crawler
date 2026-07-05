import React, { useState } from 'react'

export default function URLInput({ onSubmit, isLoading }) {
  const [url, setUrl] = useState('')
  const [maxPages, setMaxPages] = useState(50)
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    const trimmedUrl = url.trim()
    if (!trimmedUrl) {
      setError('Please enter a website URL.')
      return
    }

    try {
      const parsed = new URL(trimmedUrl)
      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        setError('URL must start with http:// or https://')
        return
      }
    } catch (_) {
      setError('Please enter a valid URL (e.g. https://docs.python.org).')
      return
    }

    onSubmit(trimmedUrl, maxPages)
  }

  return (
    <div className="card-solid animate-slide">
      <h1 style={{
        fontSize: '28px',
        fontWeight: '800',
        marginBottom: '8px',
        textAlign: 'center',
        background: 'var(--accent-gradient)',
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
      }}>
        Website Crawler Chatbot
      </h1>
      <p style={{
        color: 'var(--text-secondary)',
        fontSize: '14px',
        textAlign: 'center',
        marginBottom: '32px'
      }}>
        Crawl any website, index its pages, and query its contents using generative RAG.
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
            Website URL
          </label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            disabled={isLoading}
            className="input-solid"
            style={{
              borderColor: error ? 'var(--error)' : 'var(--border-color)'
            }}
          />
          {error && (
            <p style={{ color: 'var(--error)', fontSize: '12px', marginTop: '4px' }}>
              {error}
            </p>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: '600' }}>
            <span>Max Pages to Crawl</span>
            <span style={{ color: 'var(--accent-cyan)' }}>{maxPages} pages</span>
          </div>
          <input
            type="range"
            min="10"
            max="100"
            step="5"
            value={maxPages}
            onChange={(e) => setMaxPages(parseInt(e.target.value))}
            disabled={isLoading}
            style={{
              width: '100%',
              accentColor: 'var(--accent-cyan)',
              cursor: 'pointer',
              height: '6px',
              borderRadius: '3px',
              backgroundColor: 'var(--bg-primary)'
            }}
          />
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Limits crawl depth to respect website bandwidth and speed up indexing.
          </span>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="btn-gradient"
          style={{ width: '100%', marginTop: '8px', padding: '14px' }}
        >
          {isLoading ? (
            <>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="spinner" style={{ animation: 'spin 1s linear infinite' }}>
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeOpacity="0.2" />
                <path d="M12 2a10 10 0 0 1 10 10" />
              </svg>
              Starting Crawl...
            </>
          ) : (
            <>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M2 12a10 10 0 1 0 20 0 10 10 0 1 0-20 0M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10zM2 12h20" />
              </svg>
              Crawl & Index Website
            </>
          )}
        </button>
      </form>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
