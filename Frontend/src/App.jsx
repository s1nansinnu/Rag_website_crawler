import React, { useState } from 'react'
import { useCrawl } from './hooks/useCrawl'
import { useChat } from './hooks/useChat'
import URLInput from './components/URLInput'
import CrawlProgress from './components/CrawlProgress'
import Sidebar from './components/Sidebar'
import ChatWindow from './components/ChatWindow'
import ChatInput from './components/ChatInput'

export default function App() {
  const { startCrawl, resetCrawl, phase: crawlPhase, progress: crawlProgress, error: crawlError, sessionId, isComplete } = useCrawl()
  const { messages, isStreaming, error: chatError, sendMessage, clearMessages } = useChat()
  
  const [appPhase, setAppPhase] = useState('input') // 'input', 'crawling', 'ready'
  const [crawledUrl, setCrawledUrl] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleStartCrawl = async (url, maxPages) => {
    setCrawledUrl(url)
    setAppPhase('crawling')
    await startCrawl(url, maxPages)
  }

  const handleStartChatting = () => {
    setAppPhase('ready')
  }

  const handleNewCrawl = () => {
    resetCrawl()
    clearMessages()
    setCrawledUrl('')
    setAppPhase('input')
    setSidebarOpen(false)
  }

  const handleSendQuestion = (question) => {
    sendMessage(question, sessionId)
  }

  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev)
  }

  return (
    <div className="app-container">
      {/* 1. Input Phase */}
      {appPhase === 'input' && (
        <div className="crawl-phase-container">
          <URLInput onSubmit={handleStartCrawl} isLoading={false} />
        </div>
      )}

      {/* 2. Crawling/Progress Phase */}
      {appPhase === 'crawling' && (
        <div className="crawl-phase-container">
          <CrawlProgress
            phase={crawlPhase}
            progress={crawlProgress}
            error={crawlError}
            onStartChat={handleStartChatting}
            onReset={handleNewCrawl}
          />
        </div>
      )}

      {/* 3. Chatting/Ready Phase */}
      {appPhase === 'ready' && (
        <>
          <Sidebar
            websiteUrl={crawledUrl}
            pagesCrawled={crawlProgress.pages_crawled}
            totalChunks={crawlProgress.total_discovered} // Using discovered count as proxy
            onNewCrawl={handleNewCrawl}
            isOpen={sidebarOpen}
            onToggle={toggleSidebar}
          />

          <main className="chat-main">
            {/* Header for Chat View */}
            <header style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '16px 24px',
              backgroundColor: 'var(--bg-secondary)',
              borderBottom: '1px solid var(--border-color)',
              height: '60px',
              flexShrink: 0
            }}>
              {/* Mobile hamburger menu toggle */}
              <button
                onClick={toggleSidebar}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                  padding: '4px',
                }}
                className="md-menu-btn"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </svg>
              </button>

              <div style={{
                fontSize: '14px',
                fontWeight: '600',
                color: 'var(--text-secondary)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                maxWidth: 'calc(100% - 40px)',
                textAlign: 'right'
              }}>
                Chatting with: <span style={{ color: 'var(--accent-cyan)' }}>{crawledUrl}</span>
              </div>
            </header>

            {/* Error display if chat error */}
            {chatError && (
              <div style={{
                padding: '12px 24px',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                borderBottom: '1px solid var(--error)',
                color: '#fca5a5',
                fontSize: '13px'
              }}>
                {chatError}
              </div>
            )}

            {/* Chat Messages */}
            <ChatWindow
              messages={messages}
              isStreaming={isStreaming}
              websiteUrl={crawledUrl}
            />

            {/* Chat Input */}
            <ChatInput
              onSend={handleSendQuestion}
              isDisabled={isStreaming}
            />
          </main>
        </>
      )}

      <style>{`
        .md-menu-btn {
          display: none;
        }
        @media (max-width: 768px) {
          .md-menu-btn {
            display: block;
          }
        }
      `}</style>
    </div>
  )
}
