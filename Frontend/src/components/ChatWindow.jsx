import React, { useRef, useEffect } from 'react'
import MessageBubble from './MessageBubble'

export default function ChatWindow({ messages, isStreaming, websiteUrl }) {
  const containerRef = useRef(null)

  useEffect(() => {
    // Auto scroll to bottom
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div
      ref={containerRef}
      style={{
        flexGrow: 1,
        overflowY: 'auto',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--bg-primary)'
      }}
    >
      {messages.length === 0 ? (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          flexGrow: 1,
          color: 'var(--text-secondary)',
          textAlign: 'center',
          animation: 'fadeIn var(--transition-normal)'
        }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '16px',
            backgroundColor: 'var(--bg-secondary)',
            border: '1px solid var(--border-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '20px',
            color: 'var(--accent-cyan)'
          }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <h3 style={{ color: 'var(--text-primary)', marginBottom: '8px', fontSize: '18px', fontWeight: '600' }}>
            Chat with {websiteUrl ? new URL(websiteUrl).hostname : 'Website'}
          </h3>
          <p style={{ maxWidth: '360px', fontSize: '14px', lineHeight: '1.6' }}>
            Ask questions about the site content. The LLM will search the vector store to formulate an answer with citations.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', width: '100%', maxWidth: '900px', margin: '0 auto' }}>
          {messages.map((msg, index) => (
            <MessageBubble key={index} message={msg} />
          ))}
        </div>
      )}
    </div>
  )
}
