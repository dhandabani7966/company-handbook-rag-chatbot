import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, AlertCircle, RefreshCw, HelpCircle } from 'lucide-react';
import AnswerCard from './AnswerCard';

export default function ChatWindow({
  messages,
  onSendMessage,
  isAsking,
  indexedChunks,
  suggestedQuestions = []
}) {
  const [inputQuestion, setInputQuestion] = useState('');
  const chatViewportRef = useRef(null);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

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

  const handleSubmit = (e) => {
    e.preventDefault();
    const clean = inputQuestion.trim();
    if (!clean || isAsking || indexedChunks === 0) return;

    onSendMessage(clean);
    setInputQuestion('');
  };

  const handleSuggestionClick = (questionText) => {
    if (isAsking || indexedChunks === 0) return;
    onSendMessage(questionText);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="chat-window-container">
      {/* Messages Viewport */}
      <div className="chat-viewport" ref={chatViewportRef}>
        {messages.length === 0 ? (
          <div className="chat-empty-state">
            <div className="empty-icon-bubble">
              <Bot size={36} />
            </div>
            <h3>Handbook Intelligence Assistant</h3>
            <p className="empty-description">
              {indexedChunks > 0
                ? "Ask natural-language questions about company policies, leave entitlements, benefits, or working guidelines."
                : "Please upload and index a company handbook PDF to begin asking questions."}
            </p>

            {indexedChunks > 0 && suggestedQuestions.length > 0 && (
              <div className="suggestions-container">
                <span className="suggestions-label">
                  <Sparkles size={14} /> Example inquiries:
                </span>
                <div className="suggestions-grid">
                  {suggestedQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="suggestion-chip"
                      onClick={() => handleSuggestionClick(q)}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((msg, index) => {
              if (msg.role === 'user') {
                return (
                  <div key={index} className="user-message-row">
                    <div className="user-bubble">
                      <p>{msg.text}</p>
                      {msg.timestamp && <span className="message-time-user">{msg.timestamp}</span>}
                    </div>
                    <div className="user-avatar">
                      <User size={16} />
                    </div>
                  </div>
                );
              } else {
                return <AnswerCard key={index} message={msg} />;
              }
            })}

            {isAsking && (
              <div className="assistant-generating-bubble">
                <div className="assistant-avatar">
                  <Bot size={18} />
                </div>
                <div className="generating-indicator">
                  <RefreshCw size={14} className="spin-icon" />
                  <span>Retrieving context & formulating grounded answer...</span>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="chat-input-bar">
        {indexedChunks === 0 && (
          <div className="input-disabled-warning">
            <HelpCircle size={14} />
            <span>Upload a handbook PDF above to enable questions.</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="input-form">
          <input
            ref={inputRef}
            type="text"
            className="chat-text-input"
            placeholder={
              indexedChunks > 0
                ? "Ask a question about the handbook (e.g., 'What is the annual leave policy?')..."
                : "Handbook not indexed yet..."
            }
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isAsking || indexedChunks === 0}
            maxLength={500}
          />

          <button
            type="submit"
            className="send-button"
            disabled={!inputQuestion.trim() || isAsking || indexedChunks === 0}
            aria-label="Send question"
          >
            {isAsking ? <RefreshCw size={16} className="spin-icon" /> : <Send size={16} />}
          </button>
        </form>
        <div className="input-footer">
          <span className="footer-hint">Answers are grounded exclusively in retrieved handbook passages.</span>
          <span className="char-count">{inputQuestion.length}/500</span>
        </div>
      </div>
    </div>
  );
}
