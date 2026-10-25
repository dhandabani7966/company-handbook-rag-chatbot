import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, FileText, ExternalLink } from 'lucide-react';

export default function SourceCitation({ sources, onCitationClick }) {
  const [expandedIndices, setExpandedIndices] = useState({});

  if (!sources || sources.length === 0) {
    return null;
  }

  const toggleExpand = (idx) => {
    setExpandedIndices(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  return (
    <div className="source-citation-container">
      <div className="source-citation-header">
        <BookOpen size={14} className="source-header-icon" />
        <span className="source-header-title">Grounding Citations ({sources.length})</span>
        <span className="source-header-hint">Click pill to preview verified handbook page</span>
      </div>

      <div className="source-list">
        {sources.map((source, index) => {
          const isExpanded = !!expandedIndices[index];
          const page = source.page || source.pdf_page || '?';
          const cleanText = (source.text || '')
            .replace(/\uFFFD/g, '• ')
            .replace(/•\s*•/g, '•')
            .trim();
          const isLongText = cleanText.length > 180;
          const displayText = !isExpanded && isLongText
            ? `${cleanText.slice(0, 180)}...`
            : cleanText;

          return (
            <div key={index} className="source-item-card">
              <div className="source-meta-row">
                <button
                  type="button"
                  className="source-page-badge clickable"
                  onClick={() => onCitationClick?.(source)}
                  title="Click to view full grounded excerpt"
                >
                  <FileText size={13} color="#DC2626" />
                  <span>PDF Page {page}</span>
                  <ExternalLink size={11} className="pill-ext-icon" />
                </button>

                {isLongText && (
                  <button
                    type="button"
                    className="source-expand-btn"
                    onClick={() => toggleExpand(index)}
                  >
                    {isExpanded ? (
                      <><span>Collapse</span> <ChevronUp size={13} /></>
                    ) : (
                      <><span>Read snippet</span> <ChevronDown size={13} /></>
                    )}
                  </button>
                )}
              </div>
              <p className="source-excerpt-text">{displayText}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
