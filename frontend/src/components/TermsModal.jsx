import React from 'react';
import { X, ShieldCheck } from 'lucide-react';

export default function TermsModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="terms-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <ShieldCheck size={20} className="text-orange" />
            <h2 className="modal-heading">Privacy Notice &amp; Terms</h2>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-content terms-content">
          <h4>Data Privacy &amp; Policy Grounding</h4>
          <p>
            The Handbook AI Assistant is an internal knowledge tool designed to help employees quickly find and understand company policies.
          </p>

          <h4>1. Confidentiality</h4>
          <p>
            All employee handbook documents and user queries remain strictly local or within designated secure corporate infrastructure. No user inquiries are shared with public third-party LLM training pipelines.
          </p>

          <h4>2. Grounded Verification</h4>
          <p>
            Every answer provided by the AI is strictly extracted and synthesized from the indexed version of the Atos India Employee Policy Handbook (version 10.3). Citations to exact PDF page numbers are provided for auditing and validation.
          </p>

          <h4>3. Discrepancy &amp; Binding Precedence</h4>
          <p>
            In any scenario where an operational dispute arises, the signed HR policies, official offer letters, and direct communications from People &amp; Culture / Human Resources take precedence over automated AI summaries.
          </p>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn-primary-orange" onClick={onClose}>
            I Understand
          </button>
        </div>
      </div>
    </div>
  );
}
