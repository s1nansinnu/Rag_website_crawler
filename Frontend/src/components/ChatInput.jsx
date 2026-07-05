import React, { useState, useRef, useEffect } from 'react'

export default function ChatInput({ onSend, isDisabled }) {
  const [text, setText] = useState('')
  const textareaRef = useRef(null)

  useEffect(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [text])

  const handleSubmit = (e) => {
    if (e) e.preventDefault()
    if (!text.trim() || isDisabled) return

    onSend(text.trim())
    setText('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{
      display: 'flex',
      gap: '12px',
      alignItems: 'flex-end',
      padding: '16px 24px',
      backgroundColor: 'var(--bg-primary)',
      borderTop: '1px solid var(--border-color)',
      position: 'relative'
    }}>
      <textarea
        ref={textareaRef}
        rows="1"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={isDisabled ? 'Generating answer...' : 'Ask something about the website...'}
        disabled={isDisabled}
        style={{
          flexGrow: 1,
          backgroundColor: 'var(--bg-secondary)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--text-primary)',
          padding: '12px 16px',
          fontSize: '15px',
          fontFamily: 'inherit',
          outline: 'none',
          resize: 'none',
          maxHeight: '120px',
          transition: 'border-color var(--transition-fast)'
        }}
        onFocus={(e) => e.target.style.borderColor = 'var(--accent-cyan)'}
        onBlur={(e) => e.target.style.borderColor = 'var(--border-color)'}
      />

      <button
        type="submit"
        disabled={isDisabled || !text.trim()}
        className="btn-gradient"
        style={{
          padding: '12px',
          width: '46px',
          height: '46px',
          borderRadius: '50%',
          flexShrink: 0
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </form>
  )
}
