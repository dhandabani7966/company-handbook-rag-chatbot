import React, { useState } from 'react';
import { Trash2, Search, CheckSquare, Square, Plus, X, MessageSquare } from 'lucide-react';

export default function HistoryPanel({
  conversations = [],
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onClearHistory,
  isOpen = false,
  onClose
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [showConfirmClear, setShowConfirmClear] = useState(false);

  // Filter conversations based on user search query
  const filteredConversations = conversations.filter(conv => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    const matchTitle = conv.title?.toLowerCase().includes(query);
    const matchPreview = conv.preview?.toLowerCase().includes(query);
    return matchTitle || matchPreview;
  });

  const handleToggleSelect = (e, id) => {
    e.stopPropagation();
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleClear = () => {
    onClearHistory(selectedIds.size > 0 ? Array.from(selectedIds) : null);
    setSelectedIds(new Set());
    setShowConfirmClear(false);
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div className="history-backdrop" onClick={onClose} aria-hidden="true" />
      )}

      <aside className={`app-history-panel ${isOpen ? 'history-open' : ''}`}>
        {/* Top History Header */}
        <div className="history-header">
          <div className="history-title-row">
            <h2 className="history-heading">History</h2>
            <div className="history-actions">
              {conversations.length > 0 && (
                <button
                  type="button"
                  className="clear-all-btn"
                  onClick={() => setShowConfirmClear(true)}
                  title="Clear conversation history"
                >
                  <Trash2 size={15} />
                  <span>{selectedIds.size > 0 ? `Delete (${selectedIds.size})` : 'Clear All'}</span>
                </button>
              )}
              {/* Close button on mobile */}
              <button
                type="button"
                className="history-close-btn"
                onClick={onClose}
                aria-label="Close history panel"
              >
                <X size={18} />
              </button>
            </div>
          </div>

          {/* New Chat Button */}
          <button
            type="button"
            className="new-chat-btn"
            onClick={() => {
              onNewConversation();
              onClose?.();
            }}
          >
            <Plus size={16} />
            <span>New Chat</span>
          </button>

          {/* Search History Input */}
          <div className="history-search-wrapper">
            <Search size={15} className="history-search-icon" />
            <input
              type="text"
              className="history-search-input"
              placeholder="Search history..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                type="button"
                className="history-clear-search"
                onClick={() => setSearchQuery('')}
                aria-label="Clear search text"
              >
                <X size={13} />
              </button>
            )}
          </div>
        </div>

        {/* Conversation List */}
        <div className="history-list-container">
          {filteredConversations.length === 0 ? (
            <div className="history-empty-state">
              <MessageSquare size={26} className="history-empty-icon" />
              <p className="history-empty-text">
                {searchQuery
                  ? "No conversations match your search."
                  : "No saved chat history yet. Ask a question to begin!"}
              </p>
            </div>
          ) : (
            <div className="history-items-list">
              {filteredConversations.map((conv) => {
                const isActive = conv.id === activeConversationId;
                const isSelected = selectedIds.has(conv.id);

                return (
                  <div
                    key={conv.id}
                    className={`history-item-card ${isActive ? 'history-item-active' : ''}`}
                    onClick={() => {
                      onSelectConversation(conv.id);
                      onClose?.();
                    }}
                  >
                    <button
                      type="button"
                      className="history-checkbox-btn"
                      onClick={(e) => handleToggleSelect(e, conv.id)}
                      aria-label={`Select ${conv.title}`}
                    >
                      {isSelected ? (
                        <CheckSquare size={16} className="text-orange" />
                      ) : (
                        <Square size={16} className="text-muted" />
                      )}
                    </button>

                    <div className="history-item-details">
                      <div className="history-item-top">
                        <span className="history-item-title" title={conv.title}>
                          {conv.title || 'Conversation'}
                        </span>
                        {conv.time && (
                          <span className="history-item-time">{conv.time}</span>
                        )}
                      </div>
                      <p className="history-item-preview" title={conv.preview}>
                        {conv.preview || 'Click to view messages'}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Confirmation Modal for Clearing History */}
        {showConfirmClear && (
          <div className="modal-overlay" onClick={() => setShowConfirmClear(false)}>
            <div className="confirm-modal-card" onClick={(e) => e.stopPropagation()}>
              <h3 className="confirm-modal-title">Clear History?</h3>
              <p className="confirm-modal-body">
                {selectedIds.size > 0
                  ? `Are you sure you want to delete ${selectedIds.size} selected conversation(s)? This action cannot be undone.`
                  : "Are you sure you want to clear all conversation history? This cannot be undone."}
              </p>
              <div className="confirm-modal-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowConfirmClear(false)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn-confirm-delete"
                  onClick={handleClear}
                >
                  Confirm Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}
