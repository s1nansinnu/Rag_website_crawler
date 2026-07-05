import React from 'react'

export default function Sidebar({ websiteUrl, pagesCrawled, totalChunks, onNewCrawl, isOpen, onToggle }) {
  const getDomain = (url) => {
    try {
      return new URL(url).hostname
    } catch (_) {
      return url
    }
  }

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          onClick={onToggle}
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 99,
            display: 'block',
          }}
          className="md-hidden"
        />
      )}

      <aside
        className={`sidebar ${isOpen ? 'open' : ''}`}
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '24px',
          height: '100%',
          backgroundColor: 'var(--bg-secondary)',
          borderRight: '1px solid var(--border-color)',
          zIndex: 100
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: 'var(--accent-gradient)'
              }} />
              <span style={{ fontWeight: '700', fontSize: '16px', letterSpacing: '0.5px' }}>
                Crawler RAG
              </span>
            </div>
            {/* Mobile close button */}
            <button
              onClick={onToggle}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                padding: '4px'
              }}
              className="md-close-btn"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          {/* Active Site Info */}
          {websiteUrl && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '600', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
                Active Crawl
              </span>
              <div style={{
                backgroundColor: 'var(--bg-primary)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-md)',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
              }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Domain</span>
                  <span style={{
                    fontSize: '14px',
                    fontWeight: '600',
                    color: 'var(--text-primary)',
                    wordBreak: 'break-all'
                  }}>
                    {getDomain(websiteUrl)}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-color)', paddingTop: '12px', marginTop: '4px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Pages</span>
                    <span style={{ fontSize: '15px', fontWeight: '700', color: 'var(--accent-cyan)' }}>
                      {pagesCrawled}
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Vector Chunks</span>
                    <span style={{ fontSize: '15px', fontWeight: '700', color: 'var(--accent-purple)' }}>
                      {totalChunks}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Action button */}
        <button
          onClick={onNewCrawl}
          className="btn-gradient"
          style={{
            width: '100%',
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-primary)',
            padding: '12px',
            fontSize: '14px'
          }}
          onMouseEnter={(e) => {
            e.target.style.borderColor = 'var(--accent-cyan)'
          }}
          onMouseLeave={(e) => {
            e.target.style.borderColor = 'var(--border-color)'
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '8px', verticalAlign: 'middle' }}>
            <path d="M21 12a9 9 0 0 1-9 9m9-9a9 9 0 0 0-9-9m9 9H3m9 9a9 9 0 0 1-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
          </svg>
          New Crawl
        </button>
      </aside>

      <style>{`
        .md-hidden {
          display: none;
        }
        .md-close-btn {
          display: none;
        }
        @media (max-width: 768px) {
          .md-hidden {
            display: block;
          }
          .md-close-btn {
            display: block;
          }
          .sidebar {
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            transform: translateX(-100%);
            transition: transform 0.3s ease;
          }
          .sidebar.open {
            transform: translateX(0);
          }
        }
      `}</style>
    </>
  )
}
