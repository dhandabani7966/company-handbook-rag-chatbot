import React from 'react';
import { X, HelpCircle, ArrowRight, BookOpen, Clock, Home, Award, HeartPulse } from 'lucide-react';

export default function FaqModal({ isOpen, onClose, onSelectQuestion }) {
  if (!isOpen) return null;

  const faqs = [
    {
      category: "Leave & Attendance",
      icon: <Clock size={16} className="text-orange" />,
      question: "What is the annual leave entitlement?",
      summary: "22 working days of annual / privilege leave credited per year in advance per semester (Page 49)."
    },
    {
      category: "Leave Carry-Forward",
      icon: <Award size={16} className="text-orange" />,
      question: "What is the privilege leave carry-forward limit?",
      summary: "Up to 10 days can be carried forward per year, subject to a maximum accumulated accrual of 25 days (Page 49 & 50)."
    },
    {
      category: "Remote Work",
      icon: <Home size={16} className="text-orange" />,
      question: "What are the remote work / WFH guidelines?",
      summary: "Requires manager authorization, noise-free conducive workspace, reliable broadband & mobile connection, and UPS backup (Page 70)."
    },
    {
      category: "Health & Benefits",
      icon: <HeartPulse size={16} className="text-orange" />,
      question: "What is the policy for employee medical health checkup?",
      summary: "Atos provides preventive health checkup facilities for eligible employees as outlined in section 10.3 (Page 53)."
    },
    {
      category: "Employment Terms",
      icon: <BookOpen size={16} className="text-orange" />,
      question: "What is the policy for probation period?",
      summary: "Guidelines on lateral employee confirmation and probation periods under the employment terms chapter (Page 23)."
    }
  ];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="faq-modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title-row">
            <HelpCircle size={20} className="text-orange" />
            <h2 className="modal-heading">Updates &amp; Handbook FAQ</h2>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <div className="modal-content">
          <p className="faq-intro-text">
            Frequently referenced policies from the Atos India Employee Policy Handbook (version 10.3). Click any item to ask the AI assistant.
          </p>

          <div className="faq-grid">
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                className="faq-card-item"
                onClick={() => {
                  onSelectQuestion(faq.question);
                  onClose();
                }}
              >
                <div className="faq-card-header">
                  <div className="faq-category-tag">
                    {faq.icon}
                    <span>{faq.category}</span>
                  </div>
                  <ArrowRight size={14} className="faq-arrow-icon" />
                </div>
                <h4 className="faq-card-question">{faq.question}</h4>
                <p className="faq-card-summary">{faq.summary}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
