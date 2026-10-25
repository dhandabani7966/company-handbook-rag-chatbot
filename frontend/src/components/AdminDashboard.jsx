import React, { useState, useEffect } from 'react';
import {
  Users,
  FileBox,
  MessageSquare,
  Activity,
  ArrowLeft,
  Shield,
  HelpCircle,
  TrendingUp,
  RefreshCw,
  Clock
} from 'lucide-react';

export default function AdminDashboard({ apiBase, token, onBackToChat }) {
  const [metrics, setMetrics] = useState({
    total_users: 0,
    total_documents: 0,
    total_conversations: 0,
    total_queries: 0,
    average_feedback_rating: 0.0,
    vector_store_chunks: 0,
    rag_health: 'healthy',
    system_uptime: '99.98%'
  });
  const [activityData, setActivityData] = useState([]);
  const [topQuestions, setTopQuestions] = useState([]);
  const [usersList, setUsersList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState('');

  const loadAdminData = async () => {
    try {
      setLoading(true);
      const headers = { Authorization: `Bearer ${token}` };

      // 1. Overview metrics
      const resOverview = await fetch(`${apiBase}/api/admin/overview`, { headers });
      if (resOverview.ok) {
        const d = await resOverview.json();
        setMetrics(d.metrics);
      }

      // 2. 7-day activity & top questions
      const resActivity = await fetch(`${apiBase}/api/admin/activity`, { headers });
      if (resActivity.ok) {
        const d = await resActivity.json();
        setActivityData(d.weekly_activity || []);
        setTopQuestions(d.top_questions || []);
      }

      // 3. Users list
      const resUsers = await fetch(`${apiBase}/api/admin/users`, { headers });
      if (resUsers.ok) {
        const d = await resUsers.json();
        setUsersList(d.users || []);
      }
    } catch (err) {
      console.error('Failed to load admin analytics', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, [token]);

  const handleRoleToggle = async (userId, currentRole) => {
    const newRole = currentRole === 'admin' ? 'employee' : 'admin';
    if (!window.confirm(`Change this user's role to ${newRole}?`)) return;

    try {
      const res = await fetch(`${apiBase}/api/admin/users/${userId}/role`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ role: newRole })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Role change failed');
      setActionMsg(`Role updated to ${newRole}`);
      loadAdminData();
    } catch (err) {
      alert(err.message);
    }
  };

  // Find max conversations for bar height scaling
  const maxConv = Math.max(...activityData.map(d => d.conversations), 5);

  return (
    <div className="enterprise-page-container">
      {/* Header */}
      <div className="page-header-row">
        <div>
          <button className="back-breadcrumb-btn" onClick={onBackToChat}>
            <ArrowLeft size={16} />
            <span>Back to Chat</span>
          </button>
          <h2>Admin Dashboard</h2>
          <p className="page-subtitle">
            Platform governance, retrieval system telemetry, and user management.
          </p>
        </div>

        <div className="page-header-actions">
          <button className="secondary-action-btn" onClick={loadAdminData}>
            <RefreshCw size={16} />
            <span>Refresh Analytics</span>
          </button>
        </div>
      </div>

      {actionMsg && (
        <div className="status-toast-bar">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg('')}>✕</button>
        </div>
      )}

      {/* 4 Overview Stat Cards matching Screen 7 */}
      <div className="stats-cards-grid">
        <div className="stat-card">
          <div className="stat-card-icon-wrap total">
            <Users size={22} color="#F97316" />
          </div>
          <div className="stat-card-info">
            <span className="stat-card-label">Total Users</span>
            <h3 className="stat-card-value">{metrics.total_users}</h3>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-icon-wrap indexed">
            <FileBox size={22} color="#16A34A" />
          </div>
          <div className="stat-card-info">
            <span className="stat-card-label">Indexed Documents</span>
            <h3 className="stat-card-value">{metrics.total_documents}</h3>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-icon-wrap processing">
            <MessageSquare size={22} color="#EAB308" />
          </div>
          <div className="stat-card-info">
            <span className="stat-card-label">Conversations</span>
            <h3 className="stat-card-value">{metrics.total_conversations}</h3>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-card-icon-wrap uptime">
            <Activity size={22} color="#3B82F6" />
          </div>
          <div className="stat-card-info">
            <span className="stat-card-label">System Uptime</span>
            <h3 className="stat-card-value">{metrics.system_uptime}</h3>
          </div>
        </div>
      </div>

      {/* 2-Column Section: Left Activity Bar Chart & Right Top Questions */}
      <div className="admin-analytics-grid">
        {/* Left Bar Chart */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <div className="analytics-title-group">
              <TrendingUp size={18} color="#EA580C" />
              <h3>Conversations (Last 7 Days)</h3>
            </div>
            <span className="analytics-badge">Daily Volume</span>
          </div>

          <div className="bar-chart-container">
            {activityData.map((d, i) => {
              const heightPercent = Math.max(12, Math.round((d.conversations / maxConv) * 100));
              return (
                <div key={i} className="chart-bar-column">
                  <div className="bar-value-label">{d.conversations}</div>
                  <div className="bar-track">
                    <div
                      className="bar-fill"
                      style={{ height: `${heightPercent}%` }}
                      title={`${d.date}: ${d.conversations} conversations`}
                    ></div>
                  </div>
                  <span className="bar-day-label">{d.day}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Top Questions */}
        <div className="analytics-card">
          <div className="analytics-card-header">
            <div className="analytics-title-group">
              <HelpCircle size={18} color="#EA580C" />
              <h3>Top Policy Questions</h3>
            </div>
            <span className="analytics-badge">Frequent Topics</span>
          </div>

          <div className="top-questions-list">
            {topQuestions.length === 0 ? (
              <div className="empty-sub-state">
                <Clock size={28} color="#9CA3AF" />
                <p>No questions logged yet. Start querying to populate analytics.</p>
              </div>
            ) : (
              topQuestions.map((q, idx) => (
                <div key={idx} className="top-question-item">
                  <div className="question-rank-badge">#{idx + 1}</div>
                  <div className="question-content-wrap">
                    <span className="question-text">{q.query}</span>
                    <span className="question-meta">Asked {q.count} time{q.count !== 1 ? 's' : ''}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* User Governance Table */}
      <div className="enterprise-table-card" style={{ marginTop: '24px' }}>
        <div className="table-card-inner-header">
          <div className="title-with-icon">
            <Shield size={20} color="#EA580C" />
            <h3>User Governance & Access Control</h3>
          </div>
          <span>{usersList.length} registered user{usersList.length !== 1 ? 's' : ''}</span>
        </div>

        <table className="enterprise-data-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Current Role</th>
              <th>Registered</th>
              <th style={{ textAlign: 'right' }}>Role Action</th>
            </tr>
          </thead>
          <tbody>
            {usersList.map((u) => (
              <tr key={u.id}>
                <td>
                  <div className="user-profile-cell">
                    <div className="avatar-circle">
                      {u.full_name ? u.full_name.charAt(0).toUpperCase() : 'U'}
                    </div>
                    <strong>{u.full_name || 'Anonymous User'}</strong>
                  </div>
                </td>
                <td>{u.email}</td>
                <td>
                  <span className={`role-badge ${u.role}`}>
                    {u.role.toUpperCase()}
                  </span>
                </td>
                <td className="timestamp-cell">
                  {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}
                </td>
                <td>
                  <div className="table-actions-cell">
                    <button
                      className="secondary-action-btn small"
                      onClick={() => handleRoleToggle(u.id, u.role)}
                    >
                      {u.role === 'admin' ? 'Demote to Employee' : 'Promote to Admin'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
