import React, { useState, useRef, useEffect } from 'react';
import { Send, ArrowUp, Paperclip, Loader2, Sparkles } from 'lucide-react';

export default function ChatComposer({
  onSendMessage,
  isAsking = false,
  onOpenFileUpload,
  placeholder = "Ask anything about your company policies..."
}) {
  const [text, setText] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const textareaRef = useRef(null);

  // Auto-resize textarea height as user types (up to ~160px)
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;

    el.style.height = 'auto';
    const scrollHeight = el.scrollHeight;
    // Minimum line height ~24px, max expansion ~160px
    const newHeight = Math.min(Math.max(scrollHeight, 24), 160);
    el.style.height = `${newHeight}px`;
  }, [text]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    const cleanText = text.trim();
    if (!cleanText || isAsking) return;

    onSendMessage(cleanText);
    setText('');

    // Reset textarea height after sending
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isSendDisabled = !text.trim() || isAsking;

  return (
    <div className="chat-composer-outer">
      <form
        onSubmit={handleSubmit}
        className={`chat-composer-box ${isFocused ? 'composer-focused' : ''} ${isAsking ? 'composer-busy' : ''}`}
        onClick={() => textareaRef.current?.focus()}
      >
        {/* Multiline Question Input Area */}
        <div className="composer-input-row">
          <textarea
            ref={textareaRef}
            rows={1}
            className="composer-textarea"
            placeholder={placeholder}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            disabled={isAsking}
            aria-label="Ask a policy question"
          />
        </div>

        {/* Bottom Toolbar: Attachment on left, Send button on right */}
        <div className="composer-toolbar-row">
          <div className="composer-toolbar-left">
            {onOpenFileUpload && (
              <button
                type="button"
                className="composer-tool-btn"
                title="Upload PDF handbook to knowledge base"
                aria-label="Upload PDF handbook"
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenFileUpload();
                }}
                disabled={isAsking}
              >
                <Paperclip size={18} />
                <span className="tool-btn-label">Attach Handbook</span>
              </button>
            )}
            <span className="composer-keyboard-hint">
              <strong>Enter</strong> to send • <strong>Shift + Enter</strong> for new line
            </span>
          </div>

          <div className="composer-toolbar-right">
            <button
              type="submit"
              className={`composer-send-btn ${!isSendDisabled ? 'composer-send-active' : ''}`}
              disabled={isSendDisabled}
              aria-label={isAsking ? "Processing inquiry" : "Send inquiry"}
              title={isAsking ? "Generating answer..." : "Send message"}
              onClick={(e) => e.stopPropagation()}
            >
              {isAsking ? (
                <Loader2 size={18} className="composer-spinner" />
              ) : (
                <ArrowUp size={18} strokeWidth={2.4} />
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Grounding Disclaimer */}
      <p className="composer-disclaimer-text">
        Responses are strictly grounded in <strong>Atos India Employee Policy Handbook v10.3</strong> with page citations.
      </p>
    </div>
  );
}
