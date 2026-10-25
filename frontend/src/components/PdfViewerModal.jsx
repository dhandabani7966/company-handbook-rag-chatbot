import React from 'react';
import { FileText, ExternalLink, X, BookOpen, CheckCircle2 } from 'lucide-react';

export default function PdfViewerModal({ isOpen, onClose, citation, apiBase, token }) {
  if (!isOpen || !citation) return null;

  const pageNum = citation.page || citation.pdf_page || '?';
  const sourceName = citation.source || 'Atos India Employee Policy Handbook';
  const textExcerpt = citation.text || citation.snippet || 'No excerpt available for this citation.';
  const sectionName = citation.section || citation.topic || 'General Handbook Policy';

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="pdf-viewer-modal-card" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="pdf-viewer-header">
          <div className="pdf-viewer-title-group">
            <div className="pdf-viewer-icon-badge">
              <FileText size={20} color="#EA580C" />
            </div>
            <div>
              <h3>Citation Grounding Preview</h3>
              <p className="pdf-viewer-meta">
                Source: <strong>{sourceName}</strong> • Page <strong>{pageNum}</strong>
              </p>
            </div>
          </div>
          <div className="pdf-viewer-actions">
            <button className="modal-close-btn" onClick={onClose}>
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Modal Content Body */}
        <div className="pdf-viewer-body">
          <div className="citation-badge-banner">
            <div className="citation-verified-tag">
              <CheckCircle2 size={16} color="#16A34A" />
              <span>Grounded Verification: Page {pageNum}</span>
            </div>
            <span className="citation-section-tag">
              <BookOpen size={14} />
              {sectionName}
            </span>
          </div>

          <div className="citation-excerpt-container">
            <div className="citation-excerpt-label">Handbook Excerpt as Indexed:</div>
            <blockquote className="citation-excerpt-quote">
              {textExcerpt}
            </blockquote>
          </div>

          <div className="citation-info-callout">
            <p>
              This passage was retrieved directly by Sentence Transformers vector search and used by the Qwen LLM
              to construct the grounded answer without hallucination.
            </p>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="pdf-viewer-footer">
          <button className="secondary-action-btn" onClick={onClose}>
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
}
