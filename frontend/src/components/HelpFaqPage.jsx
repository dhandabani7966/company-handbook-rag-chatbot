import React, { useState } from 'react';
import { HelpCircle, BookOpen, ChevronDown, ChevronUp, MessageSquare, ArrowLeft, CheckCircle2 } from 'lucide-react';

export default function HelpFaqPage({ onSelectQuestion, onBackToChat }) {
  const [activeTab, setActiveTab] = useState('faq');
  const [expandedIndex, setExpandedIndex] = useState(0);

  const faqs = [
    {
      q: "What is the annual leave entitlement for full-time employees?",
      a: "According to Section 10.1.3 (PDF page 49) of the Atos India Employee Policy Handbook v10.3, employees are entitled to 22 working days of annual/privilege leave every year. Employees who join during the year receive pro-rata leave based on their start date.",
      section: "Section 10.1.3 (Page 49)"
    },
    {
      q: "How many privilege leave days can an employee carry forward?",
      a: "As defined in Section 10.1.4.1 (PDF page 49), a maximum of 10 days of privilege leave from the current year's entitlement can be carried forward to the following calendar year, subject to a maximum accumulated balance of 25 days.",
      section: "Section 10.1.4.1 (Page 49)"
    },
    {
      q: "What are the Work from Home (WFH) eligibility and approval guidelines?",
      a: "Section 14 (PDF page 70) establishes that WFH is subject to role suitability, explicit manager authorization, base-location work readiness, and compliance with information security guidelines.",
      section: "Section 14 (Page 70)"
    },
    {
      q: "How do I verify the accuracy of an answer provided by the AI?",
      a: "Every answer generated includes direct PDF citation pills (e.g. 'PDF Page 49'). Click any pill to view the exact excerpt retrieved from the indexed handbook.",
      section: "Grounded Citations"
    },
    {
      q: "What happens if a policy is not mentioned in the handbook?",
      a: "Handbook AI is strictly grounded in the indexed PDF document. If a topic is not covered in the handbook, it will explicitly state that the policy could not be found, rather than inventing unverified rules.",
      section: "Grounded Guardrail"
    }
  ];

  const guides = [
    {
      title: "1. Formulating Effective Policy Questions",
      content: "Be specific about the policy topic (e.g., 'What is the privilege leave carry-forward limit?' rather than just 'leaves'). The AI retrieves matching sections using semantic embeddings."
    },
    {
      title: "2. Inspecting Grounded Citations",
      content: "After receiving an answer, review the red citation badges below the numbered explanation. Each badge links to the exact handbook page where the policy is documented."
    },
    {
      title: "3. Managing Your Chat History",
      content: "Use the History page to revisit past queries, rename conversations for easy categorization, or delete old sessions."
    },
    {
      title: "4. Uploading New or Updated Handbooks",
      content: "Administrators can upload revised company policies in the Documents page. The system will chunk and index the PDF into ChromaDB without overwriting existing collections."
    }
  ];

  return (
    <div className="enterprise-page-container">
      {/* Header */}
      <div className="page-header-row">
        <div>
          <button className="back-breadcrumb-btn" onClick={onBackToChat}>
            <ArrowLeft size={16} />
            <span>Back to Chat</span>
          </button>
          <h2>Help & Frequently Asked Questions</h2>
          <p className="page-subtitle">Learn how to make the most of your Company Handbook Intelligence AI assistant.</p>
        </div>
      </div>

      {/* Tabs matching Screen 8 */}
      <div className="help-tabs-row">
        <button
          className={`help-tab-btn ${activeTab === 'faq' ? 'active' : ''}`}
          onClick={() => setActiveTab('faq')}
        >
          <HelpCircle size={18} />
          <span>Frequently Asked Questions</span>
        </button>
        <button
          className={`help-tab-btn ${activeTab === 'guide' ? 'active' : ''}`}
          onClick={() => setActiveTab('guide')}
        >
          <BookOpen size={18} />
          <span>User Guide & Best Practices</span>
        </button>
      </div>

      {/* Tab 1: FAQs */}
      {activeTab === 'faq' && (
        <div className="accordion-list">
          {faqs.map((faq, idx) => {
            const isExpanded = expandedIndex === idx;
            return (
              <div key={idx} className={`accordion-card ${isExpanded ? 'expanded' : ''}`}>
                <div
                  className="accordion-header"
                  onClick={() => setExpandedIndex(isExpanded ? -1 : idx)}
                >
                  <div className="accordion-title-row">
                    <span className="accordion-q-num">Q{idx + 1}</span>
                    <span className="accordion-question-text">{faq.q}</span>
                  </div>
                  <div className="accordion-toggle-icon">
                    {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </div>

                {isExpanded && (
                  <div className="accordion-body">
                    <p className="accordion-answer">{faq.a}</p>
                    <div className="accordion-footer">
                      <span className="accordion-source-tag">
                        <CheckCircle2 size={14} color="#16A34A" />
                        Grounded in: {faq.section}
                      </span>
                      <button
                        className="ask-this-btn"
                        onClick={() => onSelectQuestion(faq.q)}
                      >
                        <MessageSquare size={14} />
                        <span>Ask AI in Chat</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Tab 2: User Guide */}
      {activeTab === 'guide' && (
        <div className="user-guide-grid">
          {guides.map((g, idx) => (
            <div key={idx} className="guide-card">
              <h4>{g.title}</h4>
              <p>{g.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
