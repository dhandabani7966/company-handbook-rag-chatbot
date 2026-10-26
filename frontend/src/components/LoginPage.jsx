import React, { useState, useEffect } from 'react';
import { signup, login, getSettings, oauthLogin, requestPasswordRecovery, updateUser, acceptInvite } from '@netlify/identity';
import { Bot, CheckCircle, Lock, Mail, ArrowRight, User, Eye, EyeOff, ShieldAlert } from 'lucide-react';

export default function LoginPage({ onLoginSuccess, authError, callback, onResetComplete }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [notice, setNotice] = useState('');
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const resetting = callback?.type === 'recovery' || callback?.type === 'invite';
  useEffect(() => { getSettings().then(settings => setGoogleEnabled(Boolean(settings.providers.google))).catch(() => {}); }, []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotMsg, setForgotMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (resetting) {
        const user = callback.type === 'invite'
          ? await acceptInvite(callback.token, password)
          : await updateUser({ password });
        onResetComplete();
        onLoginSuccess(user);
      } else if (isRegister) {
        const user = await signup(email.trim(), password, { full_name: fullName.trim() });
        if (user.confirmedAt) onLoginSuccess(user);
        else {
          setNotice('Account created. Check your email and follow the confirmation link before signing in.');
          setIsRegister(false);
          setPassword('');
        }
      } else {
        onLoginSuccess(await login(email.trim(), password));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!forgotEmail) return;
    try {
      await requestPasswordRecovery(forgotEmail.trim());
      setForgotMsg('If an account exists with this email, check your inbox for password reset instructions.');
    } catch (err) {
      setForgotMsg('Error requesting password reset.');
    }
  };

  return (
    <div className="login-screen-wrapper">
      {/* Left Hero Graphic Section */}
      <div className="login-hero-panel">
        <div className="login-hero-brand">
          <div className="brand-badge-icon">
            <Bot size={28} color="#FFFFFF" />
          </div>
          <div className="brand-badge-text">
            <h2>Handbook AI</h2>
            <span>Your Policy Assistant</span>
          </div>
        </div>

        <div className="login-hero-content">
          <h1>Instant, Grounded Workplace Answers</h1>
          <p>
            Trained directly on Atos India Employee Policy Handbook v10.3. Get verified answers with exact page citations in seconds.
          </p>

          <div className="login-features-list">
            <div className="login-feature-item">
              <CheckCircle size={20} className="feature-check" />
              <div>
                <strong>100% Grounded Answers</strong>
                <p>Every claim is retrieved directly from official company handbook sections.</p>
              </div>
            </div>
            <div className="login-feature-item">
              <CheckCircle size={20} className="feature-check" />
              <div>
                <strong>Page-Accurate Citations</strong>
                <p>Click on any citation pill to inspect the source paragraph and page number.</p>
              </div>
            </div>
            <div className="login-feature-item">
              <CheckCircle size={20} className="feature-check" />
              <div>
                <strong>Enterprise Role Governance</strong>
                <p>Full support for HR administrator knowledge management and employee queries.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="login-hero-footer">
          <span>Enterprise Edition v2.0 • ISO 27001 Compliant</span>
        </div>
      </div>

      {/* Right Form Section */}
      <div className="login-form-panel">
        <div className="login-form-container">
          <div className="login-header">
            {!resetting && <div className="login-toggle-prompt">
              <span>{isRegister ? 'Already have an account?' : "Don't have an account?"}</span>
              <button
                type="button"
                className="link-btn"
                onClick={() => {
                  setIsRegister(!isRegister);
                  setError('');
                  setNotice('');
                }}
              >
                {isRegister ? 'Sign In' : 'Sign Up'}
              </button>
            </div>}

            <h2>{resetting ? 'Set Your Password' : isRegister ? 'Create Your Account' : 'Welcome Back'}</h2>
            <p className="login-subtitle">
              {isRegister
                ? 'Join your team and get instant access to company policies.'
                : 'Sign in to access your company policies and guidelines.'}
            </p>
          </div>

          {notice && <div className="alert-box success" role="status">{notice}</div>}
          {authError && <div className="login-error-alert" role="alert">{authError}</div>}

          {error && (
            <div className="login-error-alert" role="alert">
              <ShieldAlert size={18} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="login-actual-form">
            {isRegister && !resetting && (
              <div className="form-group">
                <label>Full Name</label>
                <div className="input-with-icon">
                  <User size={18} className="input-icon" />
                  <input
                    type="text"
                    minLength={2}
                    maxLength={100}
                    required
                    placeholder="e.g. Abhishek Kumar"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>
              </div>
            )}

            {!resetting && <div className="form-group">
              <label>Email Address</label>
              <div className="input-with-icon">
                <Mail size={18} className="input-icon" />
                <input
                  type="email"
                  required
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>}

            <div className="form-group">
              <div className="form-label-row">
                <label>Password</label>
                {!isRegister && !resetting && (
                  <button
                    type="button"
                    className="forgot-pass-link"
                    onClick={() => setShowForgot(true)}
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="input-with-icon">
                <Lock size={18} className="input-icon" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  minLength={isRegister || resetting ? 6 : undefined}
                  autoComplete={isRegister || resetting ? "new-password" : "current-password"}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <button type="submit" className="login-submit-btn" disabled={loading}>
              {loading ? (
                <span>Authenticating...</span>
              ) : (
                <>
                  <span>{resetting ? 'Save Password' : isRegister ? 'Create Account' : 'Sign In'}</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>
          </form>

          {/* Social SSO Button */}
          {googleEnabled && !resetting && <>
          <div className="sso-divider">
            <span>Or continue with SSO</span>
          </div>
          <button
            type="button"
            className="sso-signin-btn"
            onClick={() => { try { oauthLogin('google'); } catch (err) { setError(err.message); } }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>Sign in with Company Single Sign-On (SSO)</span>
          </button>

          </>}
          <p className="login-terms-note">
            By signing in, you agree to the company's Information Security Guidelines and Data Privacy Policy.
          </p>
        </div>
      </div>

      {/* Forgot Password Modal */}
      {showForgot && (
        <div className="modal-backdrop" onClick={() => setShowForgot(false)}>
          <div className="modal-content-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Reset Your Password</h3>
              <button className="modal-close-btn" onClick={() => setShowForgot(false)}>✕</button>
            </div>
            <form onSubmit={handleForgotPassword} className="modal-body-form">
              <p>Enter your work email address to receive password reset instructions.</p>
              <div className="form-group">
                <input
                  type="email"
                  required
                  placeholder="name@company.com"
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                />
              </div>
              {forgotMsg && <div className="alert-box success">{forgotMsg}</div>}
              <button type="submit" className="primary-action-btn">Send Reset Link</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
