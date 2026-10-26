import React, { useState, useEffect } from 'react';
import {
  User,
  Lock,
  Sliders,
  Bell,
  Palette,
  Cpu,
  Shield,
  CheckCircle,
  Save,
  ArrowLeft,
  KeyRound
} from 'lucide-react';

export default function SettingsPage({ apiBase, token, currentUser, onUpdateUser, onBackToChat }) {
  const [activeTab, setActiveTab] = useState('profile');
  const [fullName, setFullName] = useState(currentUser?.full_name || '');
  const [email] = useState(currentUser?.email || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [theme, setTheme] = useState('system');
  const [fontSize, setFontSize] = useState('medium');
  const [emailNotif, setEmailNotif] = useState(true);
  const [chatSound, setChatSound] = useState(true);
  const [analyticsOptIn, setAnalyticsOptIn] = useState(true);
  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' });
  const [saving, setSaving] = useState(false);

  // Load preferences from backend
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await fetch(`${apiBase}/api/settings`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          if (data.theme) setTheme(data.theme);
          if (data.font_size) setFontSize(data.font_size);
          if (data.email_notifications !== undefined) setEmailNotif(data.email_notifications);
          if (data.chat_sound !== undefined) setChatSound(data.chat_sound);
          if (data.analytics_opt_in !== undefined) setAnalyticsOptIn(data.analytics_opt_in);
        }
      } catch (err) {
        console.warn('Could not fetch user settings', err);
      }
    };
    if (token) fetchSettings();
  }, [token]);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    setStatusMsg({ type: '', text: '' });
    try {
      const res = await fetch(`${apiBase}/api/auth/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ full_name: fullName })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to update profile');
      onUpdateUser({ ...currentUser, full_name: fullName });
      setStatusMsg({ type: 'success', text: 'Profile updated successfully!' });
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message });
    } finally {
      setSaving(false);
    }
  };

  const handleSavePassword = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setStatusMsg({ type: 'error', text: 'New passwords do not match' });
      return;
    }
    if (newPassword.length < 6) {
      setStatusMsg({ type: 'error', text: 'Password must be at least 6 characters' });
      return;
    }
    setSaving(true);
    setStatusMsg({ type: '', text: '' });
    try {
      const res = await fetch(`${apiBase}/api/auth/change-password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ old_password: currentPassword, new_password: newPassword })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Password change failed');
      setStatusMsg({ type: 'success', text: 'Password changed successfully!' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message });
    } finally {
      setSaving(false);
    }
  };

  const handleSavePreferences = async () => {
    setSaving(true);
    setStatusMsg({ type: '', text: '' });
    try {
      const res = await fetch(`${apiBase}/api/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          theme,
          font_size: fontSize,
          email_notifications: emailNotif,
          chat_sound: chatSound,
          analytics_opt_in: analyticsOptIn
        })
      });
      if (res.ok) {
        setStatusMsg({ type: 'success', text: 'Preferences saved!' });
      }
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message });
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Lock },
    { id: 'chat_pref', label: 'Chat Preferences', icon: Sliders },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'application', label: 'Application', icon: Cpu },
    { id: 'privacy', label: 'Privacy', icon: Shield }
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
          <h2>Settings & Preferences</h2>
          <p className="page-subtitle">Configure your account, AI preferences, and application parameters.</p>
        </div>
      </div>

      {statusMsg.text && (
        <div className={`status-toast-bar ${statusMsg.type}`}>
          <span>{statusMsg.text}</span>
          <button onClick={() => setStatusMsg({ type: '', text: '' })}>✕</button>
        </div>
      )}

      {/* Settings Grid matching Screen 6 */}
      <div className="settings-layout-grid">
        {/* Vertical Sub-Nav Sidebar */}
        <div className="settings-subnav-card">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                className={`settings-nav-btn ${isActive ? 'active' : ''}`}
                onClick={() => {
                  setActiveTab(tab.id);
                  setStatusMsg({ type: '', text: '' });
                }}
              >
                <Icon size={18} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Panel */}
        <div className="settings-content-card">
          {/* 1. Profile Tab */}
          {activeTab === 'profile' && (
            <div className="settings-tab-pane">
              <h3>Profile Information</h3>
              <p className="tab-pane-desc">Manage your display name and view your enterprise role privileges.</p>

              <form onSubmit={handleSaveProfile} className="settings-form">
                <div className="form-group">
                  <label>Full Name</label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Email Address</label>
                  <input type="email" disabled value={email} className="readonly-input" />
                  <span className="input-hint">Your email is managed by company SSO directory.</span>
                </div>

                <div className="form-group">
                  <label>Enterprise Role</label>
                  <div className="role-display-row">
                    <span className="role-badge-pill">{currentUser?.role?.toUpperCase() || 'EMPLOYEE'}</span>
                    <span className="role-description">
                      {currentUser?.role === 'admin'
                        ? 'Full administrative rights to manage documents, users, and audit logs.'
                        : 'Access to chat assistant and public company handbook knowledge base.'}
                    </span>
                  </div>
                </div>

                <div className="form-actions-row">
                  <button type="submit" className="primary-action-btn" disabled={saving}>
                    <Save size={16} />
                    <span>{saving ? 'Saving...' : 'Save Profile Changes'}</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* 2. Security Tab */}
          {activeTab === 'security' && (
            <div className="settings-tab-pane">
              <h3>Password & Security</h3>
              <p className="tab-pane-desc">Update your password to keep your workplace account secure.</p>

              <form onSubmit={handleSavePassword} className="settings-form">
                <div className="form-group">
                  <label>Current Password</label>
                  <input
                    type="password"
                    required
                    placeholder="Enter current password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>New Password</label>
                  <input
                    type="password"
                    required
                    placeholder="At least 6 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Confirm New Password</label>
                  <input
                    type="password"
                    required
                    placeholder="Re-type new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                </div>

                <div className="form-actions-row">
                  <button type="submit" className="primary-action-btn" disabled={saving}>
                    <KeyRound size={16} />
                    <span>{saving ? 'Updating...' : 'Update Password'}</span>
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* 3. Chat Preferences Tab */}
          {activeTab === 'chat_pref' && (
            <div className="settings-tab-pane">
              <h3>Chat Preferences</h3>
              <p className="tab-pane-desc">Customize how responses are formatted and presented.</p>

              <div className="settings-form">
                <div className="form-group">
                  <label>Font Size</label>
                  <div className="choice-buttons-row">
                    {['small', 'medium', 'large'].map((size) => (
                      <button
                        key={size}
                        type="button"
                        className={`choice-btn ${fontSize === size ? 'active' : ''}`}
                        onClick={() => setFontSize(size)}
                      >
                        {size.charAt(0).toUpperCase() + size.slice(1)}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="form-group switch-group">
                  <div>
                    <strong>Chat Audio Alerts</strong>
                    <p className="input-hint">Play subtle sound chime when AI completes answer generation.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={chatSound}
                    onChange={(e) => setChatSound(e.target.checked)}
                  />
                </div>

                <div className="form-actions-row">
                  <button type="button" className="primary-action-btn" onClick={handleSavePreferences} disabled={saving}>
                    <Save size={16} />
                    <span>Save Chat Preferences</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 4. Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="settings-tab-pane">
              <h3>Notifications</h3>
              <p className="tab-pane-desc">Manage your notification channels and policy digest emails.</p>

              <div className="settings-form">
                <div className="form-group switch-group">
                  <div>
                    <strong>Email Notifications</strong>
                    <p className="input-hint">Receive policy revision notices and HR updates.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={emailNotif}
                    onChange={(e) => setEmailNotif(e.target.checked)}
                  />
                </div>

                <div className="form-actions-row">
                  <button type="button" className="primary-action-btn" onClick={handleSavePreferences} disabled={saving}>
                    <Save size={16} />
                    <span>Save Notification Settings</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 5. Appearance Tab */}
          {activeTab === 'appearance' && (
            <div className="settings-tab-pane">
              <h3>Appearance & Theme</h3>
              <p className="tab-pane-desc">Choose between system default, light, or high-contrast theme.</p>

              <div className="settings-form">
                <div className="theme-options-grid">
                  {[
                    { id: 'system', label: 'System Default', desc: 'Syncs with OS preferences' },
                    { id: 'light', label: 'Clean Light', desc: 'Crisp white workspace with orange accents' },
                    { id: 'dark', label: 'Midnight Dark', desc: 'Sleek dark interface for late-night review' }
                  ].map((t) => (
                    <div
                      key={t.id}
                      className={`theme-card ${theme === t.id ? 'active' : ''}`}
                      onClick={() => setTheme(t.id)}
                    >
                      <strong>{t.label}</strong>
                      <p>{t.desc}</p>
                    </div>
                  ))}
                </div>

                <div className="form-actions-row">
                  <button type="button" className="primary-action-btn" onClick={handleSavePreferences} disabled={saving}>
                    <Save size={16} />
                    <span>Apply Theme</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* 6. Application Tab */}
          {activeTab === 'application' && (
            <div className="settings-tab-pane">
              <h3>Application Architecture</h3>
              <p className="tab-pane-desc">Technical parameters of the local RAG engine.</p>

              <div className="system-specs-table">
                <div className="spec-row">
                  <span className="spec-label">Backend Host</span>
                  <span className="spec-val">{apiBase || 'http://127.0.0.1:8000'}</span>
                </div>
                <div className="spec-row">
                  <span className="spec-label">Embedding Model</span>
                  <span className="spec-val">all-MiniLM-L6-v2 (384-dimensional dense vectors)</span>
                </div>
                <div className="spec-row">
                  <span className="spec-label">Vector Database</span>
                  <span className="spec-val">ChromaDB Persistent (Cosine Similarity)</span>
                </div>
                <div className="spec-row">
                  <span className="spec-label">LLM Engine</span>
                  <span className="spec-val">Local Qwen (Grounded Generation)</span>
                </div>
                <div className="spec-row">
                  <span className="spec-label">Target Document</span>
                  <span className="spec-val">Atos India Employee Policy Handbook v10.3 (378 chunks)</span>
                </div>
              </div>
            </div>
          )}

          {/* 7. Privacy Tab */}
          {activeTab === 'privacy' && (
            <div className="settings-tab-pane">
              <h3>Privacy & Data Retention</h3>
              <p className="tab-pane-desc">Enterprise data governance and confidentiality compliance.</p>

              <div className="settings-form">
                <div className="form-group switch-group">
                  <div>
                    <strong>Anonymous Query Telemetry</strong>
                    <p className="input-hint">Allow anonymous latency and retrieval score aggregation to improve search accuracy.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={analyticsOptIn}
                    onChange={(e) => setAnalyticsOptIn(e.target.checked)}
                  />
                </div>

                <div className="danger-zone-box">
                  <h4>Data Management</h4>
                  <p>Clear cached conversation data from your local browser browser storage.</p>
                  <button
                    type="button"
                    className="danger-action-btn"
                    onClick={() => {
                      if (window.confirm('Clear all local browser cached data?')) {
                        localStorage.clear();
                        window.location.reload();
                      }
                    }}
                  >
                    Clear Local Browser Cache
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
