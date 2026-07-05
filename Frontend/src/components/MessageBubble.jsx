import React from 'react'

export default function MessageBubble({ message }) {
  const { role, content, sources } = message
  const isUser = role === 'user'

  const parseMarkdown = (text) => {
    if (!text) return null
    
    // Split by code blocks
    const parts = text.split(/(```[\s\S]*?```)/g)
    
    return parts.map((part, index) => {
      if (part.startsWith('```')) {
        const match = part.match(/```(\w*)\n([\s\S]*?)```/)
        const code = match ? match[2] : part.slice(3, -3)
        return (
          <pre key={index} style={{
            backgroundColor: 'var(--bg-primary)',
            border: '1px solid var(--border-color)',
            padding: '12px',
            borderRadius: 'var(--radius-md)',
            overflowX: 'auto',
            margin: '12px 0',
            fontFamily: 'var(--font-mono)',
            fontSize: '13px',
            color: '#f8fafc'
          }}>
            <code>{code.trim()}</code>
          </pre>
        )
      } else {
        const lines = part.split('\n')
        return (
          <span key={index}>
            {lines.map((line, lineIdx) => {
              const isBullet = line.trim().startsWith('* ') || line.trim().startsWith('- ')
              let lineText = isBullet ? line.trim().substring(2) : line

              // Simple bold, italic, inline code replacements
              let html = lineText
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code style="background-color: var(--bg-primary); padding: 2px 6px; border-radius: 4px; font-family: var(--font-mono); font-size: 0.9em; color: var(--accent-cyan);">$1</code>')

              if (isBullet) {
                return (
                  <li key={lineIdx} style={{ marginLeft: '20px', marginBottom: '6px', listStyleType: 'disc' }} dangerouslySetInnerHTML={{ __html: html }} />
                )
              }

              // Return paragraph if not empty
              return line.trim() ? (
                <p key={lineIdx} style={{ marginBottom: lineIdx === lines.length - 1 ? 0 : '10px' }} dangerouslySetInnerHTML={{ __html: html }} />
              ) : (
                <div key={lineIdx} style={{ height: '8px' }} />
              )
            })}
          </span>
        )
      }
    })
  }

  // Get domain name from URL for cleaner display
  const getDomainLabel = (url) => {
    try {
      const parsed = new URL(url)
      const path = parsed.pathname === '/' ? '' : parsed.pathname
      // Return hostname + path snippet (max 25 chars)
      const display = parsed.hostname + path
      return display.length > 25 ? display.substring(0, 22) + '...' : display
    } catch (_) {
      return url
    }
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
      gap: '6px',
      width: '100%',
      animation: 'fadeIn 0.25s ease-out forwards',
      marginBottom: '16px'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        maxWidth: '80%',
        flexDirection: isUser ? 'row-reverse' : 'row'
      }}>
        {/* Avatar */}
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          background: isUser ? 'var(--accent-gradient)' : 'var(--bg-tertiary)',
          border: isUser ? 'none' : '1px solid var(--border-color)',
          color: '#fff'
        }}>
          {isUser ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="10" rx="2" />
              <circle cx="12" cy="5" r="2" />
              <path d="M12 7v4" />
              <line x1="8" y1="16" x2="8.01" y2="16" />
              <line x1="16" y1="16" x2="16.01" y2="16" />
            </svg>
          )}
        </div>

        {/* Message Bubble Card */}
        <div style={{
          backgroundColor: isUser ? 'var(--bg-tertiary)' : 'var(--bg-secondary)',
          border: '1px solid',
          borderColor: isUser ? 'var(--accent-purple)' : 'var(--border-color)',
          borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
          padding: '14px 18px',
          fontSize: '15px',
          color: 'var(--text-primary)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div className="markdown-body">
            {content ? parseMarkdown(content) : (
              // Bouncing dots typing indicator
              <div style={{ display: 'flex', gap: '4px', padding: '6px 0', alignItems: 'center' }}>
                <span className="dot" style={{ width: '6px', height: '6px', backgroundColor: 'var(--text-secondary)', borderRadius: '50%', display: 'inline-block', animation: 'bounce 1.4s infinite ease-in-out both' }} />
                <span className="dot" style={{ width: '6px', height: '6px', backgroundColor: 'var(--text-secondary)', borderRadius: '50%', display: 'inline-block', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.2s' }} />
                <span className="dot" style={{ width: '6px', height: '6px', backgroundColor: 'var(--text-secondary)', borderRadius: '50%', display: 'inline-block', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.4s' }} />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Sources list */}
      {!isUser && sources && sources.length > 0 && (
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px',
          paddingLeft: '44px',
          marginTop: '4px',
          maxWidth: '80%'
        }}>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', alignSelf: 'center' }}>Sources:</span>
          {sources.map((url, index) => (
            <a
              key={index}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              title={url}
              style={{
                fontSize: '11px',
                color: 'var(--accent-cyan)',
                backgroundColor: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                padding: '3px 8px',
                borderRadius: '12px',
                textDecoration: 'none',
                transition: 'all var(--transition-fast)'
              }}
              onMouseEnter={(e) => {
                e.target.style.borderColor = 'var(--accent-cyan)'
                e.target.style.backgroundColor = 'var(--bg-tertiary)'
              }}
              onMouseLeave={(e) => {
                e.target.style.borderColor = 'var(--border-color)'
                e.target.style.backgroundColor = 'var(--bg-secondary)'
              }}
            >
              {getDomainLabel(url)}
            </a>
          ))}
        </div>
      )}

      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1.0); }
        }
      `}</style>
    </div>
  )
}
