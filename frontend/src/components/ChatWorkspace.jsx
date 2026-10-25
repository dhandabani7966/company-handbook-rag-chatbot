import React, { useState, useRef, useEffect } from 'react';
import {
  Bot,
  User,
  Search,
  Sparkles,
  Menu,
  Clock
} from 'lucide-react';
import AnswerCard from './AnswerCard';
import ChatComposer from './ChatComposer';

export default function ChatWorkspace({
  messages = [],
  onSendMessage,
  isAsking = false,
  indexedChunks = 0,
  currentDocument = null,
  suggestedQuestions = [],
  onOpenSidebar,
  onOpenHistory,
  onCitationClick,
  onOpenFileUpload
}) {
  const [searchFilter, setSearchFilter] = useState('');
  const chatViewportRef = useRef(null);

  // Auto-scroll to bottom as messages arrive
  useEffect(() => {
    const timer = setTimeout(() => {
      if (chatViewportRef.current) {
        chatViewportRef.current.scrollTo({
          top: chatViewportRef.current.scrollHeight,
          behavior: 'smooth'
        });
      }
    }, 60);
    return () => clearTimeout(timer);
  }, [messages, isAsking]);

  // Filter messages if searchFilter is set
  const filteredMessages = messages.filter(msg => {
    if (!searchFilter.trim()) return true;
    const query = searchFilter.toLowerCase();
    if (msg.role === 'user') return msg.text?.toLowerCase().includes(query);
    return msg.answer?.toLowerCase().includes(query);
  });

  return (
    <div className="chat-workspace-panel">
      {/* Workspace Header */}
      <header className="workspace-header">
        <div className="header-left">
          {/* Mobile sidebar toggle button */}
          <button
            type="button"
            className="mobile-nav-toggle"
            onClick={onOpenSidebar}
            aria-label="Open navigation sidebar"
          >
            <Menu size={20} />
          </button>

          <div className="workspace-titles">
            <h1 className="workspace-title">
              Ask <span className="text-orange">Anything</span>
            </h1>
            <p className="workspace-subtitle">
              Instant policy answers grounded in Atos India Employee Policy Handbook v10.3
            </p>
          </div>
        </div>

        <div className="header-right">


          {/* Conversation Search Field */}
          <div className="conversation-search-box">
            <Search size={16} className="search-box-icon" />
            <input
              type="text"
              className="search-box-input"
              placeholder="Search chat..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
            />
          </div>

          {/* Mobile history toggle button */}
          <button
            type="button"
            className="mobile-history-toggle"
            onClick={onOpenHistory}
            aria-label="Open chat history"
          >
            <Clock size={20} />
          </button>
        </div>
      </header>

      {/* Chat Messages Viewport */}
      <div className="chat-viewport" ref={chatViewportRef}>
        {messages.length === 0 ? (
          <div className="chat-empty-state">
            <div className="assistant-avatar-large">
              <Bot size={38} color="#FFFFFF" strokeWidth={2.2} />
            </div>
            <h2 className="empty-title">Hello! How can I assist you today?</h2>
            <p className="empty-subtitle">
              Ask any question about annual leave entitlement, privilege leave carry-forward, work from home guidelines, probation period, or code of conduct.
            </p>

            {suggestedQuestions.length > 0 && (
              <div className="suggestions-container">
                <span className="suggestions-label">
                  <Sparkles size={14} className="text-orange" /> Recommended Inquiries:
                </span>
                <div className="suggestions-grid">
                  {suggestedQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="suggestion-chip"
                      onClick={() => onSendMessage(q)}
                      disabled={isAsking}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="messages-flow">
            {filteredMessages.map((msg, idx) => {
              if (msg.role === 'user') {
                return (
                  <div key={idx} className="user-message-row">
                    <div className="user-bubble">
                      <p className="user-text">{msg.text}</p>
                      {msg.timestamp && (
                        <span className="message-time-user">{msg.timestamp}</span>
                      )}
                    </div>
                    <div className="user-avatar-circle" title="Employee">
                      <User size={16} color="#FFFFFF" />
                    </div>
                  </div>
                );
              } else {
                return (
                  <div key={idx} className="assistant-message-row">
                    <div className="assistant-avatar-circle" title="Handbook AI Assistant">
                      <Bot size={18} color="#FFFFFF" strokeWidth={2.2} />
                    </div>
                    <AnswerCard message={msg} onCitationClick={onCitationClick} />
                  </div>
                );
              }
            })}

            {/* In-flight typing/retrieval indicator */}
            {isAsking && (
              <div className="assistant-message-row">
                <div className="assistant-avatar-circle assistant-avatar-pulse">
                  <Bot size={18} color="#FFFFFF" strokeWidth={2.2} />
                </div>
                <div className="assistant-bubble-card assistant-typing-bubble">
                  <div className="typing-dots">
                    <span className="dot" />
                    <span className="dot" />
                    <span className="dot" />
                  </div>
                  <span className="retrieving-label">Retrieving verified handbook sections & synthesizing grounded answer...</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modern Enterprise Chat Composer */}
      <ChatComposer
        onSendMessage={onSendMessage}
        isAsking={isAsking}
        onOpenFileUpload={onOpenFileUpload}
        placeholder="Ask anything about your company policies..."
      />
    </div>
  );
}
