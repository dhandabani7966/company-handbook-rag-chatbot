import React, { useState, useRef, useEffect } from 'react';
import {
  BookOpen,
  MessageSquare,
  History,
  FileBox,
  HelpCircle,
  Settings,
  Star,
  Shield,
  Plus,
  ChevronRight,
  LogOut,
  X,
  User as UserIcon
} from 'lucide-react';

export default function Sidebar({
  activeNav = 'chat',
  setActiveNav,
  onNewChat,
  currentUser,
  onLogout,
  isOpen = false,
  onClose
}) {
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const menuRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setShowProfileMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navItems = [
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'history', label: 'History', icon: History },
    { id: 'documents', label: 'Documents', icon: FileBox },
    { id: 'help', label: 'Help & FAQ', icon: HelpCircle },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'feedback', label: 'Feedback', icon: Star }
  ];

  if (currentUser?.role === 'admin') {
    navItems.push({ id: 'admin', label: 'Admin', icon: Shield });
  }

  const initial = currentUser?.full_name ? currentUser.full_name.charAt(0).toUpperCase() : 'A';
  const displayName = currentUser?.full_name || 'Abhishek';
  const roleName = currentUser?.role === 'admin' ? 'Administrator' : 'Employee';

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div className="sidebar-backdrop" onClick={onClose} aria-hidden="true" />
      )}

      <aside className={`app-sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        {/* Top Header / Brand */}
        <div className="sidebar-brand-container">
          <div className="sidebar-brand" onClick={() => setActiveNav('chat')} style={{ cursor: 'pointer' }}>
            <div className="brand-logo-icon">
              <BookOpen size={24} color="#FFFFFF" strokeWidth={2.3} />
            </div>
            <div className="brand-text">
              <h1 className="brand-title">Handbook <span className="brand-accent">AI</span></h1>
              <p className="brand-subtitle">Your Policy Assistant</p>
            </div>
          </div>

          {/* Mobile close button */}
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={onClose}
            aria-label="Close navigation sidebar"
          >
            <X size={20} />
          </button>
        </div>

        {/* New Chat Primary Button */}
        <div className="sidebar-action-wrap">
          <button
            type="button"
            className="sidebar-new-chat-btn"
            onClick={() => {
              onNewChat();
              setActiveNav('chat');
              onClose?.();
            }}
          >
            <Plus size={18} strokeWidth={2.5} />
            <span>New Chat</span>
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeNav === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`nav-item ${isActive ? 'nav-item-active' : ''}`}
                onClick={() => {
                  setActiveNav(item.id);
                  onClose?.();
                }}
              >
                <Icon size={19} className="nav-icon" />
                <span className="nav-label">{item.label}</span>
                {isActive && <div className="nav-active-pill" />}
              </button>
            );
          })}
        </nav>

        {/* Subtle Wave Graphic at bottom */}
        <div className="sidebar-wave-container" aria-hidden="true">
          <svg className="sidebar-wave" viewBox="0 0 240 180" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M0 120C40 90 80 150 140 100C180 65 210 110 240 85V180H0V120Z"
              fill="url(#sidebarWaveGrad1)"
              opacity="0.35"
            />
            <path
              d="M0 140C60 110 100 160 160 120C200 95 220 130 240 110V180H0V140Z"
              fill="url(#sidebarWaveGrad2)"
              opacity="0.25"
            />
            <defs>
              <linearGradient id="sidebarWaveGrad1" x1="0" y1="0" x2="240" y2="180" gradientUnits="userSpaceOnUse">
                <stop stopColor="#F97316" stopOpacity="0.8" />
                <stop offset="1" stopColor="#7C2D12" stopOpacity="0" />
              </linearGradient>
              <linearGradient id="sidebarWaveGrad2" x1="0" y1="0" x2="240" y2="180" gradientUnits="userSpaceOnUse">
                <stop stopColor="#EA580C" stopOpacity="0.9" />
                <stop offset="1" stopColor="#171717" stopOpacity="0" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        {/* Bottom User Profile Section with Screen 11 Popover */}
        <div className="sidebar-footer" ref={menuRef}>
          {showProfileMenu && (
            <div className="profile-popover-menu">
              <div className="popover-user-header">
                <strong>{displayName}</strong>
                <span className="popover-email">{currentUser?.email || 'user@company.com'}</span>
                <span className="popover-role-badge">{roleName}</span>
              </div>
              <div className="popover-divider"></div>
              <button
                type="button"
                className="popover-menu-item"
                onClick={() => {
                  setActiveNav('settings');
                  setShowProfileMenu(false);
                  onClose?.();
                }}
              >
                <UserIcon size={16} />
                <span>My Profile</span>
              </button>
              <button
                type="button"
                className="popover-menu-item"
                onClick={() => {
                  setActiveNav('settings');
                  setShowProfileMenu(false);
                  onClose?.();
                }}
              >
                <Settings size={16} />
                <span>Settings</span>
              </button>
              <button
                type="button"
                className="popover-menu-item"
                onClick={() => {
                  setActiveNav('help');
                  setShowProfileMenu(false);
                  onClose?.();
                }}
              >
                <HelpCircle size={16} />
                <span>Help & FAQ</span>
              </button>
              <button
                type="button"
                className="popover-menu-item"
                onClick={() => {
                  setActiveNav('feedback');
                  setShowProfileMenu(false);
                  onClose?.();
                }}
              >
                <Star size={16} />
                <span>Give Feedback</span>
              </button>
              <div className="popover-divider"></div>
              <button
                type="button"
                className="popover-menu-item danger"
                onClick={() => {
                  setShowProfileMenu(false);
                  onLogout();
                }}
              >
                <LogOut size={16} />
                <span>Sign Out</span>
              </button>
            </div>
          )}

          <div
            className="user-profile-card"
            onClick={() => setShowProfileMenu(!showProfileMenu)}
            title="Click to view account menu"
          >
            <div className="user-avatar-circle">
              <span>{initial}</span>
            </div>
            <div className="user-profile-info">
              <span className="user-profile-name">{displayName}</span>
              <span className="user-profile-role">{roleName}</span>
            </div>
            <ChevronRight
              size={17}
              className={`user-profile-arrow ${showProfileMenu ? 'arrow-rotate' : ''}`}
            />
          </div>
        </div>
      </aside>
    </>
  );
}
