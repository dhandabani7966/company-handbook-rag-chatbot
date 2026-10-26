import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatWorkspace from './components/ChatWorkspace';
import HistoryPanel from './components/HistoryPanel';
import HistoryPage from './components/HistoryPage';
import DocumentsPage from './components/DocumentsPage';
import SettingsPage from './components/SettingsPage';
import AdminDashboard from './components/AdminDashboard';
import HelpFaqPage from './components/HelpFaqPage';
import FeedbackPage from './components/FeedbackPage';
import LoginPage from './components/LoginPage';
import PdfViewerModal from './components/PdfViewerModal';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const STORAGE_KEY = 'handbook_ai_conversations_v3';
const ACTIVE_CONV_KEY = 'handbook_ai_active_conv_v3';
const TOKEN_KEY = 'handbook_ai_token_v3';
const USER_KEY = 'handbook_ai_user_v3';

export default function App() {
  // Auth state
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '');
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const u = localStorage.getItem(USER_KEY);
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  });

  // Navigation views: 'chat', 'history', 'documents', 'help', 'settings', 'feedback', 'admin'
  const [activeNav, setActiveNav] = useState('chat');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  // Citation Preview Modal State
  const [activeCitation, setActiveCitation] = useState(null);
  const [isCitationModalOpen, setIsCitationModalOpen] = useState(false);

  // System State
  const [backendReady, setBackendReady] = useState(false);
  const [indexedChunks, setIndexedChunks] = useState(378);
  const [currentDocument, setCurrentDocument] = useState('Atos India Employee Policy Handbook v10.3');
  const [isAsking, setIsAsking] = useState(false);

  // Conversations State
  const [conversations, setConversations] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.warn("Failed to parse local conversations", e);
    }
    const initialId = 'conv-' + Date.now();
    return [
      {
        id: initialId,
        title: 'Chat 1',
        preview: 'New inquiry session with Handbook AI',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        messages: []
      }
    ];
  });

  const [activeConvId, setActiveConvId] = useState(() => {
    try {
      const savedActive = localStorage.getItem(ACTIVE_CONV_KEY);
      if (savedActive) return savedActive;
    } catch (e) {
      console.warn("Failed to parse active conversation ID", e);
    }
    return conversations[0]?.id || 'conv-1';
  });

  // Persist conversations
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
      localStorage.setItem(ACTIVE_CONV_KEY, activeConvId);
    } catch (e) {
      console.warn("Failed to persist conversations", e);
    }
  }, [conversations, activeConvId]);

  // Auth persistence
  const handleLoginSuccess = (user, accessToken) => {
    setToken(accessToken);
    setCurrentUser(user);
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    setActiveNav('chat');
  };

  const handleLogout = () => {
    setToken('');
    setCurrentUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  };

  const handleUpdateUser = (updated) => {
    setCurrentUser(updated);
    localStorage.setItem(USER_KEY, JSON.stringify(updated));
  };

  // Health and System Check
  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        const data = await res.json();
        setBackendReady(true);
        if (data.indexed_chunks) setIndexedChunks(data.indexed_chunks);
        if (data.current_document) setCurrentDocument(data.current_document);
      }
    } catch (err) {
      setBackendReady(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Suggested questions from Atos India Handbook facts
  const sampleSuggestions = [
    "What is the annual leave entitlement?",
    "What is the privilege leave carry-forward limit?",
    "What are the remote work / WFH guidelines?",
    "What is the policy for probation period?"
  ];

  const activeConversation = conversations.find(c => c.id === activeConvId) || conversations[0];
  const messages = activeConversation?.messages || [];

  const handleNewConversation = () => {
    const newId = 'conv-' + Date.now();
    const newIndex = conversations.length + 1;
    const newConv = {
      id: newId,
      title: `Chat ${newIndex}`,
      preview: 'New inquiry session with Handbook AI',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      messages: []
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveConvId(newId);
    setActiveNav('chat');
  };

  const handleSelectConversation = (id) => {
    setActiveConvId(id);
    setActiveNav('chat');
  };

  const handleDeleteConversation = (id) => {
    setConversations(prev => {
      const remaining = prev.filter(c => c.id !== id);
      if (remaining.length === 0) {
        const freshId = 'conv-' + Date.now();
        const freshConv = {
          id: freshId,
          title: 'Chat 1',
          preview: 'New inquiry session with Handbook AI',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          messages: []
        };
        setActiveConvId(freshId);
        return [freshConv];
      }
      if (activeConvId === id) {
        setActiveConvId(remaining[0].id);
      }
      return remaining;
    });
  };

  const handleRenameConversation = (id, newTitle) => {
    setConversations(prev =>
      prev.map(c => (c.id === id ? { ...c, title: newTitle } : c))
    );
  };

  const handleClearAllHistory = () => {
    const freshId = 'conv-' + Date.now();
    const freshConv = {
      id: freshId,
      title: 'Chat 1',
      preview: 'New inquiry session with Handbook AI',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      messages: []
    };
    setConversations([freshConv]);
    setActiveConvId(freshId);
  };

  const handleCitationClick = (citation) => {
    setActiveCitation(citation);
    setIsCitationModalOpen(true);
  };

  const handleSendMessage = async (question) => {
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Add user message to conversation
    const userMsg = {
      role: 'user',
      text: question,
      timestamp: timeStr
    };

    setConversations(prev =>
      prev.map(c => {
        if (c.id === activeConvId) {
          const updatedTitle = c.messages.length === 0 ? (question.length > 32 ? question.slice(0, 30) + '...' : question) : c.title;
          return {
            ...c,
            title: updatedTitle,
            preview: question,
            time: timeStr,
            messages: [...c.messages, userMsg]
          };
        }
        return c;
      })
    );

    setIsAsking(true);

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ question })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `Server error (${res.status})`);

      const assistantMsg = {
        role: 'assistant',
        answer: data.answer,
        sources: data.sources || [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        timing: data.timing || {},
        isError: false
      };

      setConversations(prev =>
        prev.map(c => {
          if (c.id === activeConvId) {
            return {
              ...c,
              messages: [...c.messages, assistantMsg],
              preview: data.answer?.slice(0, 50) + '...'
            };
          }
          return c;
        })
      );
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        answer: `Could not retrieve answer: ${err.message}`,
        sources: [],
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true
      };

      setConversations(prev =>
        prev.map(c => {
          if (c.id === activeConvId) {
            return {
              ...c,
              messages: [...c.messages, errorMsg]
            };
          }
          return c;
        })
      );
    } finally {
      setIsAsking(false);
    }
  };

  // If not logged in, render Screen 1 (LoginPage)
  if (!token || !currentUser) {
    return (
      <LoginPage
        onLoginSuccess={handleLoginSuccess}
        apiBase={API_BASE}
      />
    );
  }

  return (
    <div className="app-saas-layout">
      {/* 1. Left Sidebar (Screen 2 & Screen 11) */}
      <Sidebar
        activeNav={activeNav}
        setActiveNav={setActiveNav}
        onNewChat={handleNewConversation}
        currentUser={currentUser}
        onLogout={handleLogout}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* 2. Main Content Area */}
      <main className="app-workspace-area">
        {activeNav === 'chat' && (
          <ChatWorkspace
            messages={messages}
            onSendMessage={handleSendMessage}
            isAsking={isAsking}
            indexedChunks={indexedChunks}
            currentDocument={currentDocument}
            suggestedQuestions={sampleSuggestions}
            onOpenSidebar={() => setIsSidebarOpen(true)}
            onOpenHistory={() => setIsHistoryOpen(true)}
            onCitationClick={handleCitationClick}
            onOpenFileUpload={() => setActiveNav('documents')}
          />
        )}

        {activeNav === 'history' && (
          <HistoryPage
            conversations={conversations}
            onSelectConversation={handleSelectConversation}
            onDeleteConversation={handleDeleteConversation}
            onRenameConversation={handleRenameConversation}
            onClearAll={handleClearAllHistory}
            onBackToChat={() => setActiveNav('chat')}
          />
        )}

        {activeNav === 'documents' && (
          <DocumentsPage
            apiBase={API_BASE}
            token={token}
            onBackToChat={() => setActiveNav('chat')}
            userRole={currentUser?.role}
          />
        )}

        {activeNav === 'settings' && (
          <SettingsPage
            apiBase={API_BASE}
            token={token}
            currentUser={currentUser}
            onUpdateUser={handleUpdateUser}
            onBackToChat={() => setActiveNav('chat')}
          />
        )}

        {activeNav === 'admin' && (
          <AdminDashboard
            apiBase={API_BASE}
            token={token}
            onBackToChat={() => setActiveNav('chat')}
          />
        )}

        {activeNav === 'help' && (
          <HelpFaqPage
            onSelectQuestion={(q) => {
              setActiveNav('chat');
              handleSendMessage(q);
            }}
            onBackToChat={() => setActiveNav('chat')}
          />
        )}

        {activeNav === 'feedback' && (
          <FeedbackPage
            apiBase={API_BASE}
            token={token}
            onBackToChat={() => setActiveNav('chat')}
          />
        )}
      </main>

      {/* 3. Right History Panel (Collapsible drawer for Chat view) */}
      {activeNav === 'chat' && (
        <HistoryPanel
          conversations={conversations}
          activeConversationId={activeConvId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onClearHistory={(ids) => {
            if (ids && ids.length > 0) {
              ids.forEach(id => handleDeleteConversation(id));
            } else {
              handleClearAllHistory();
            }
          }}
          isOpen={isHistoryOpen}
          onClose={() => setIsHistoryOpen(false)}
        />
      )}

      {/* 4. PDF Citation Preview Modal (Screen 3) */}
      <PdfViewerModal
        isOpen={isCitationModalOpen}
        onClose={() => setIsCitationModalOpen(false)}
        citation={activeCitation}
        apiBase={API_BASE}
        token={token}
      />
    </div>
  );
}
