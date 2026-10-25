import React, { useState } from 'react';
import { Search, Trash2, Edit3, MessageSquare, ExternalLink, AlertTriangle, ArrowLeft, CheckSquare, Square } from 'lucide-react';

export default function HistoryPage({
  conversations,
  onSelectConversation,
  onDeleteConversation,
  onRenameConversation,
  onClearAll,
  onBackToChat
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);
  const [renameId, setRenameId] = useState(null);
  const [renameTitle, setRenameTitle] = useState('');
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 8;

  // Filter conversations
  const filtered = conversations.filter(c => {
    const term = searchTerm.toLowerCase();
    const titleMatch = (c.title || '').toLowerCase().includes(term);
    const prevMatch = (c.preview || '').toLowerCase().includes(term);
    return titleMatch || prevMatch;
  });

  // Pagination calculation
  const totalPages = Math.ceil(filtered.length / pageSize) || 1;
  const paginated = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const toggleSelectAll = () => {
    if (selectedIds.length === paginated.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(paginated.map(c => c.id));
    }
  };

  const toggleSelectOne = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  const handleStartRename = (c) => {
    setRenameId(c.id);
    setRenameTitle(c.title || '');
  };

  const handleSaveRename = (id) => {
    if (renameTitle.trim()) {
      onRenameConversation(id, renameTitle.trim());
    }
    setRenameId(null);
  };

  const handleBulkDelete = () => {
    if (selectedIds.length === 0) return;
    selectedIds.forEach(id => onDeleteConversation(id));
    setSelectedIds([]);
  };

  return (
    <div className="enterprise-page-container">
      {/* Page Header */}
      <div className="page-header-row">
        <div>
          <button className="back-breadcrumb-btn" onClick={onBackToChat}>
            <ArrowLeft size={16} />
            <span>Back to Chat</span>
          </button>
          <h2>Chat History</h2>
          <p className="page-subtitle">Review, search, and manage your policy inquiries and AI responses.</p>
        </div>

        <div className="page-header-actions">
          {selectedIds.length > 0 && (
            <button className="danger-action-btn" onClick={handleBulkDelete}>
              <Trash2 size={16} />
              <span>Delete Selected ({selectedIds.length})</span>
            </button>
          )}
          <button className="secondary-action-btn" onClick={() => setShowClearConfirm(true)}>
            <Trash2 size={16} />
            <span>Clear All History</span>
          </button>
        </div>
      </div>

      {/* Search Toolbar */}
      <div className="table-toolbar-row">
        <div className="table-search-input">
          <Search size={18} className="search-icon" />
          <input
            type="text"
            placeholder="Search conversations by title or topic..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
          />
        </div>
        <div className="table-meta-counts">
          <span>{filtered.length} total conversation{filtered.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* History Table */}
      <div className="enterprise-table-card">
        {paginated.length === 0 ? (
          <div className="empty-table-state">
            <MessageSquare size={40} color="#9CA3AF" />
            <h3>No conversations found</h3>
            <p>Start a new chat to ask questions about the employee handbook.</p>
            <button className="primary-action-btn" onClick={onBackToChat}>
              Start New Chat
            </button>
          </div>
        ) : (
          <table className="enterprise-data-table">
            <thead>
              <tr>
                <th style={{ width: '40px' }}>
                  <button className="checkbox-toggle" onClick={toggleSelectAll}>
                    {selectedIds.length === paginated.length && paginated.length > 0 ? (
                      <CheckSquare size={18} color="#EA580C" />
                    ) : (
                      <Square size={18} color="#9CA3AF" />
                    )}
                  </button>
                </th>
                <th>Conversation Title</th>
                <th>Last Inquiry Preview</th>
                <th>Date / Time</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginated.map((c) => {
                const isSelected = selectedIds.includes(c.id);
                return (
                  <tr key={c.id} className={isSelected ? 'selected-row' : ''}>
                    <td>
                      <button className="checkbox-toggle" onClick={() => toggleSelectOne(c.id)}>
                        {isSelected ? (
                          <CheckSquare size={18} color="#EA580C" />
                        ) : (
                          <Square size={18} color="#9CA3AF" />
                        )}
                      </button>
                    </td>
                    <td>
                      {renameId === c.id ? (
                        <div className="table-inline-edit">
                          <input
                            type="text"
                            value={renameTitle}
                            autoFocus
                            onChange={(e) => setRenameTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') handleSaveRename(c.id);
                              if (e.key === 'Escape') setRenameId(null);
                            }}
                          />
                          <button className="save-btn" onClick={() => handleSaveRename(c.id)}>Save</button>
                          <button className="cancel-btn" onClick={() => setRenameId(null)}>✕</button>
                        </div>
                      ) : (
                        <div className="conversation-title-cell" onClick={() => onSelectConversation(c.id)}>
                          <MessageSquare size={16} className="title-cell-icon" />
                          <span className="title-text">{c.title || 'Untitled Chat'}</span>
                        </div>
                      )}
                    </td>
                    <td className="preview-cell">
                      <span>{c.preview || 'No messages yet'}</span>
                    </td>
                    <td className="timestamp-cell">
                      <span>{c.time || c.updated_at || 'Just now'}</span>
                    </td>
                    <td>
                      <div className="table-actions-cell">
                        <button
                          className="table-icon-btn"
                          title="Open in Chat"
                          onClick={() => onSelectConversation(c.id)}
                        >
                          <ExternalLink size={16} />
                        </button>
                        <button
                          className="table-icon-btn"
                          title="Rename"
                          onClick={() => handleStartRename(c)}
                        >
                          <Edit3 size={16} />
                        </button>
                        <button
                          className="table-icon-btn danger"
                          title="Delete"
                          onClick={() => onDeleteConversation(c.id)}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="table-pagination-row">
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <div className="pagination-buttons">
            <button
              className="page-nav-btn"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            >
              Previous
            </button>
            <button
              className="page-nav-btn"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Clear All Confirmation Modal */}
      {showClearConfirm && (
        <div className="modal-backdrop" onClick={() => setShowClearConfirm(false)}>
          <div className="modal-content-card small" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="warning-title-row">
                <AlertTriangle size={22} color="#DC2626" />
                <h3>Clear All Chat History?</h3>
              </div>
            </div>
            <p className="modal-confirm-body">
              This will permanently delete all your past conversations and questions. This action cannot be undone.
            </p>
            <div className="modal-confirm-actions">
              <button className="secondary-action-btn" onClick={() => setShowClearConfirm(false)}>
                Cancel
              </button>
              <button
                className="danger-action-btn"
                onClick={() => {
                  onClearAll();
                  setShowClearConfirm(false);
                }}
              >
                Yes, Delete All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
