import React from 'react'

export default function CrawlProgress({ phase, progress, error, onStartChat, onReset }) {
  const steps = [
    { key: 'crawling', label: 'Crawl Website Pages' },
    { key: 'chunking', label: 'Split HTML into Chunks' },
    { key: 'embedding', label: 'Generate Embeddings' },
    { key: 'complete', label: 'Ready to Chat' }
  ]

  const getStepStatus = (stepKey) => {
    if (phase === 'error') {
      if (stepKey === 'crawling' && progress.pages_crawled > 0) return 'complete'
      return 'idle'
    }

    const phaseOrder = ['idle', 'crawling', 'chunking', 'embedding', 'complete']
    const currentIndex = phaseOrder.indexOf(phase)
    const stepIndex = phaseOrder.indexOf(stepKey)

    if (phase === 'complete') return 'complete'
    if (stepIndex < currentIndex) return 'complete'
    if (stepKey === phase) return 'active'
    return 'idle'
  }

  // Calculate generic progress percentage for display
  const getProgressPercentage = () => {
    switch (phase) {
      case 'crawling':
        // Just show a pulse/indeterminate or an estimated crawl progress
        return Math.min((progress.pages_crawled / 30) * 100, 95)
      case 'chunking':
        return 95
      case 'embedding':
        return 98
      case 'complete':
        return 100
      default:
        return 0
    }
  }

  return (
    <div className="card-solid animate-slide" style={{ maxWidth: '500px' }}>
      <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '24px', textAlign: 'center' }}>
        {phase === 'error' ? 'Crawl Failed' : phase === 'complete' ? 'Index Ready' : 'Indexing Website...'}
      </h2>

      {/* Progress Bar */}
      {phase !== 'error' && (
        <div style={{
          width: '100%',
          height: '6px',
          backgroundColor: 'var(--bg-primary)',
          borderRadius: '3px',
          overflow: 'hidden',
          marginBottom: '32px',
          position: 'relative'
        }}>
          <div style={{
            width: `${getProgressPercentage()}%`,
            height: '100%',
            background: 'var(--accent-gradient)',
            borderRadius: '3px',
            transition: 'width 0.5s ease',
            position: 'relative'
          }} />
        </div>
      )}

      {/* Steps List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '32px' }}>
        {steps.map((step, idx) => {
          const status = getStepStatus(step.key)
          return (
            <div key={step.key} style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              {/* Indicator Circle */}
              <div style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '2px solid',
                backgroundColor: status === 'complete' ? 'var(--success)' : 'transparent',
                borderColor: status === 'complete' ? 'var(--success)' : status === 'active' ? 'var(--accent-cyan)' : 'var(--border-color)',
                color: status === 'complete' ? '#fff' : status === 'active' ? 'var(--accent-cyan)' : 'var(--text-muted)',
                fontSize: '12px',
                fontWeight: '700',
                transition: 'all 0.3s ease'
              }}>
                {status === 'complete' ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : status === 'active' ? (
                  <div style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--accent-cyan)',
                    animation: 'pulse 1.5s infinite'
                  }} />
                ) : (
                  idx + 1
                )}
              </div>

              {/* Label */}
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{
                  fontSize: '14px',
                  fontWeight: status === 'active' || status === 'complete' ? '600' : '400',
                  color: status === 'active' ? 'var(--text-primary)' : status === 'complete' ? 'var(--text-primary)' : 'var(--text-muted)'
                }}>
                  {step.label}
                </span>

                {/* Subtext info for active states */}
                {step.key === 'crawling' && status === 'active' && (
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px', wordBreak: 'break-all' }}>
                    Crawled {progress.pages_crawled} pages...
                  </span>
                )}
                {step.key === 'embedding' && status === 'active' && (
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    Embedding text chunks via Gemini...
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Crawl Stats & Details */}
      {phase === 'crawling' && progress.current_url && (
        <div style={{
          backgroundColor: 'var(--bg-primary)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 16px',
          fontSize: '12px',
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-secondary)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          marginBottom: '24px'
        }}>
          <span style={{ color: 'var(--accent-cyan)' }}>GET </span>
          {progress.current_url}
        </div>
      )}

      {/* Action Buttons */}
      {phase === 'complete' && (
        <button className="btn-gradient" onClick={onStartChat} style={{ width: '100%', padding: '14px' }}>
          Start Chatting
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </button>
      )}

      {phase === 'error' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid var(--error)',
            borderRadius: 'var(--radius-md)',
            padding: '16px',
            fontSize: '13px',
            color: '#fca5a5'
          }}>
            {error || 'An error occurred during indexing.'}
          </div>
          <button className="btn-gradient" onClick={onReset} style={{ width: '100%', padding: '14px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}>
            Try Again
          </button>
        </div>
      )}
    </div>
  )
}
