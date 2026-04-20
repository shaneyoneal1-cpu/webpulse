import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { Activity, Eye, EyeOff, Sun, Moon, KeyRound, Lock, User } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';

export default function Login() {
  const { login, changePassword, setupTotp, verifyTotp, mustChangePassword, totpRequired, totpSetupRequired } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const [totpSetupData, setTotpSetupData] = useState<{ secret: string; qr_uri: string } | null>(null);
  const [setupCode, setSetupCode] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const result = await login(username, password, totpCode || undefined);
      if (!result.must_change_password && !result.totp_required && !result.totp_setup_required) {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleTotpLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password, totpCode);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid TOTP code');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const result = await changePassword(null, newPassword);
      if (!result.totp_setup_required) {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  const handleSetupTotp = async () => {
    setError('');
    setLoading(true);
    try {
      const data = await setupTotp();
      setTotpSetupData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to setup TOTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifySetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await verifyTotp(setupCode);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  const renderContent = () => {
    if (mustChangePassword) {
      return (
        <form onSubmit={handleChangePassword} className="space-y-5">
          <div className="text-center mb-6">
            <div className="w-14 h-14 rounded-2xl gradient-pink flex items-center justify-center mx-auto mb-4">
              <Lock className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Change Password</h2>
            <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
              Please set a new password for your account
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>New Password</label>
            <input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-xl text-sm" required minLength={8}
              style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
              placeholder="Min 8 characters" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>Confirm Password</label>
            <input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-xl text-sm" required
              style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
              placeholder="Repeat password" />
          </div>
          {error && <p className="text-red-400 text-sm text-center">{error}</p>}
          <button type="submit" disabled={loading}
            className="w-full gradient-pink text-white py-3 rounded-xl font-semibold hover:shadow-lg hover:shadow-pink-500/25 transition-all disabled:opacity-50">
            {loading ? 'Saving...' : 'Set New Password'}
          </button>
        </form>
      );
    }

    if (totpSetupRequired) {
      if (!totpSetupData) {
        return (
          <div className="space-y-5 text-center">
            <div className="w-14 h-14 rounded-2xl gradient-pink flex items-center justify-center mx-auto mb-4">
              <KeyRound className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Setup Two-Factor Auth</h2>
            <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
              Two-factor authentication is required for security. Set up your authenticator app now.
            </p>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <button onClick={handleSetupTotp} disabled={loading}
              className="w-full gradient-pink text-white py-3 rounded-xl font-semibold hover:shadow-lg hover:shadow-pink-500/25 transition-all disabled:opacity-50">
              {loading ? 'Setting up...' : 'Setup TOTP'}
            </button>
          </div>
        );
      }

      return (
        <form onSubmit={handleVerifySetup} className="space-y-5">
          <div className="text-center mb-4">
            <div className="w-14 h-14 rounded-2xl gradient-pink flex items-center justify-center mx-auto mb-4">
              <KeyRound className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Scan QR Code</h2>
            <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
              Scan with your authenticator app (Google Authenticator, Authy, etc.)
            </p>
          </div>
          <div className="flex justify-center p-4 rounded-xl" style={{ background: '#ffffff' }}>
            <QRCodeSVG value={totpSetupData.qr_uri} size={200} />
          </div>
          <div className="rounded-xl p-3 text-center" style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-secondary)' }}>Manual entry key:</p>
            <code className="text-sm font-mono text-pink-500 break-all">{totpSetupData.secret}</code>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>Verification Code</label>
            <input type="text" value={setupCode} onChange={e => setSetupCode(e.target.value)}
              className="w-full px-4 py-3 rounded-xl text-sm text-center tracking-widest font-mono" required
              style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
              placeholder="000000" maxLength={6} />
          </div>
          {error && <p className="text-red-400 text-sm text-center">{error}</p>}
          <button type="submit" disabled={loading}
            className="w-full gradient-pink text-white py-3 rounded-xl font-semibold hover:shadow-lg hover:shadow-pink-500/25 transition-all disabled:opacity-50">
            {loading ? 'Verifying...' : 'Verify & Enable'}
          </button>
        </form>
      );
    }

    if (totpRequired) {
      return (
        <form onSubmit={handleTotpLogin} className="space-y-5">
          <div className="text-center mb-6">
            <div className="w-14 h-14 rounded-2xl gradient-pink flex items-center justify-center mx-auto mb-4">
              <KeyRound className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Two-Factor Auth</h2>
            <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>
              Enter the 6-digit code from your authenticator app
            </p>
          </div>
          <div>
            <input type="text" value={totpCode} onChange={e => setTotpCode(e.target.value)}
              className="w-full px-4 py-4 rounded-xl text-lg text-center tracking-[0.5em] font-mono" required
              style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
              placeholder="000000" maxLength={6} autoFocus />
          </div>
          {error && <p className="text-red-400 text-sm text-center">{error}</p>}
          <button type="submit" disabled={loading}
            className="w-full gradient-pink text-white py-3 rounded-xl font-semibold hover:shadow-lg hover:shadow-pink-500/25 transition-all disabled:opacity-50">
            {loading ? 'Verifying...' : 'Verify'}
          </button>
        </form>
      );
    }

    return (
      <form onSubmit={handleLogin} className="space-y-5">
        <div className="text-center mb-6">
          <div className="w-14 h-14 rounded-2xl gradient-pink flex items-center justify-center mx-auto mb-4">
            <Activity className="w-7 h-7 text-white" />
          </div>
          <h2 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>Sign in to WebPulse</h2>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Monitor your websites with confidence</p>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>Username</label>
          <div className="relative">
            <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
            <input type="text" value={username} onChange={e => setUsername(e.target.value)}
              className="w-full pl-11 pr-4 py-3 rounded-xl text-sm"
              style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
              placeholder="Enter username" required />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>Password</label>
          <div className="relative">
            <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-secondary)' }} />
            <input type={showPassword ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)}
              className="w-full pl-11 pr-12 py-3 rounded-xl text-sm"
              style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
              placeholder="Enter password" required />
            <button type="button" onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3.5 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-secondary)' }}>
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>
        {error && <p className="text-red-400 text-sm text-center">{error}</p>}
        <button type="submit" disabled={loading}
          className="w-full gradient-pink text-white py-3 rounded-xl font-semibold hover:shadow-lg hover:shadow-pink-500/25 transition-all disabled:opacity-50">
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>
    );
  };