import React, { useState } from 'react';
import { AlertCircle, ShieldCheck, Copy, Check, ThumbsUp, ThumbsDown, Zap } from 'lucide-react';
import SourceCitation from './SourceCitation';

export default function AnswerCard({ message, onCitationClick }) {
  const { answer, sources, timestamp, isError, timing } = message;
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState(null); // 'like' | 'dislike' | null

  const handleCopy = () => {
    if (!answer) return;
    navigator.clipboard.writeText(answer).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  // Helper to render text with markdown bold (e.g. **Heading:**)
  const renderFormattedText = (text) => {
    if (!text) return null;
    const paragraphs = text.split('\n\n');
    return paragraphs.map((para, pIdx) => {
      // Split by bold markdown **...**
      const parts = para.split(/(\*\*.*?\*\*)/g);
      return (
        <p key={pIdx} className="answer-paragraph">
          {parts.map((part, idx) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              const strongText = part.slice(2, -2);
              return <strong key={idx} className="answer-bold-heading">{strongText}</strong>;
            }
            return <span key={idx}>{part}</span>;
          })}
        </p>
      );
    });
  };

  const totalTime = timing?.total_sec || timing?.total || null;

  return (
    <div className={`assistant-bubble-card ${isError ? 'assistant-bubble-error' : ''}`}>
      {/* Answer Content */}
      <div className="assistant-bubble-body">
        {isError ? (
          <div className="error-content-row">
            <AlertCircle size={18} className="error-icon text-danger" />
            <p className="answer-text error-text">{answer}</p>
          </div>
        ) : (
          <div className="answer-text">
            {renderFormattedText(answer)}
          </div>
        )}
      </div>

      {/* Grounding Citations */}
      {!isError && sources && sources.length > 0 && (
        <SourceCitation sources={sources} onCitationClick={onCitationClick} />
      )}

      {/* Footer Meta & Interaction Tools */}
      <div className="bubble-footer-meta">
        <div className="footer-left-meta">
          {timestamp && <span className="message-time">{timestamp}</span>}
          {!isError && sources && sources.length > 0 && (
            <span className="grounded-tag">
              <ShieldCheck size={12} className="text-emerald" />
              <span>Grounded in Handbook</span>
            </span>
          )}
          {totalTime && (
            <span className="latency-tag">
              <Zap size={11} color="#EA580C" />
              <span>{totalTime}s</span>
            </span>
          )}
        </div>

        {!isError && (
          <div className="footer-actions">
            <button
              type="button"
              className="footer-tool-btn"
              title="Copy Answer"
              onClick={handleCopy}
            >
              {copied ? <Check size={14} color="#16A34A" /> : <Copy size={14} />}
            </button>
            <button
              type="button"
              className={`footer-tool-btn ${feedback === 'like' ? 'active-like' : ''}`}
              title="Helpful"
              onClick={() => setFeedback(feedback === 'like' ? null : 'like')}
            >
              <ThumbsUp size={14} />
            </button>
            <button
              type="button"
              className={`footer-tool-btn ${feedback === 'dislike' ? 'active-dislike' : ''}`}
              title="Not Helpful"
              onClick={() => setFeedback(feedback === 'dislike' ? null : 'dislike')}
            >
              <ThumbsDown size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
