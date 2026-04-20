import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import api from '../utils/api';

interface User {
  id: number;
  username: string;
  is_main_admin: boolean;
  totp_enabled: boolean;
  permissions: Record<string, boolean>;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  mustChangePassword: boolean;
  totpRequired: boolean;
  totpSetupRequired: boolean;
}

interface AuthContextType extends AuthState {
  login: (username: string, password: string, totpCode?: string) => Promise<any>;
  logout: () => void;
  changePassword: (currentPassword: string | null, newPassword: string) => Promise<any>;
  setupTotp: () => Promise<any>;
  verifyTotp: (code: string) => Promise<any>;
  refreshUser: () => Promise<void>;
  setToken: (token: string) => void;
  setMustChangePassword: (v: boolean) => void;
  setTotpRequired: (v: boolean) => void;
  setTotpSetupRequired: (v: boolean) => void;
  hasPermission: (perm: string) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem('webpulse_token'),
    loading: true,
    mustChangePassword: false,
    totpRequired: false,
    totpSetupRequired: false,
  });

  const refreshUser = async () => {
    try {
      const res = await api.get('/api/auth/me');
      setState(s => ({ ...s, user: res.data, loading: false }));
    } catch {
      setState(s => ({ ...s, user: null, loading: false }));
    }
  };

  useEffect(() => {
    if (state.token && !state.mustChangePassword && !state.totpRequired && !state.totpSetupRequired) {
      refreshUser();
    } else {
      setState(s => ({ ...s, loading: false }));
    }
  }, [state.token, state.mustChangePassword, state.totpRequired, state.totpSetupRequired]);

  const login = async (username: string, password: string, totpCode?: string) => {
    const res = await api.post('/api/auth/login', { username, password, totp_code: totpCode });
    const data = res.data;
    localStorage.setItem('webpulse_token', data.access_token);
    setState(s => ({
      ...s,
      token: data.access_token,
      mustChangePassword: data.must_change_password || false,
      totpRequired: data.totp_required || false,
      totpSetupRequired: data.totp_setup_required || false,
    }));
    return data;
  };

  const logout = () => {
    localStorage.removeItem('webpulse_token');
    setState({ user: null, token: null, loading: false, mustChangePassword: false, totpRequired: false, totpSetupRequired: false });
  };

  const changePassword = async (currentPassword: string | null, newPassword: string) => {
    const res = await api.post('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    const data = res.data;
    if (data.access_token) {
      localStorage.setItem('webpulse_token', data.access_token);
      setState(s => ({
        ...s,
        token: data.access_token,
        mustChangePassword: false,
        totpSetupRequired: data.totp_setup_required || false,
      }));
    }
    return data;
  };

  const setupTotp = async () => {
    const res = await api.get('/api/auth/totp/setup');
    return res.data;
  };

  const verifyTotp = async (code: string) => {
    const res = await api.post('/api/auth/totp/verify', { code });
    const data = res.data;
    if (data.access_token) {
      localStorage.setItem('webpulse_token', data.access_token);
      setState(s => ({
        ...s,
        token: data.access_token,
        totpRequired: false,
        totpSetupRequired: false,
      }));
    }
    return data;
  };

  const setToken = (token: string) => {
    localStorage.setItem('webpulse_token', token);
    setState(s => ({ ...s, token }));
  };

  const hasPermission = (perm: string) => {
    if (!state.user) return false;
    if (state.user.is_main_admin) return true;
    return state.user.permissions?.[perm] || false;
  };

  return (
    <AuthContext.Provider value={{
      ...state,
      login, logout, changePassword, setupTotp, verifyTotp,
      refreshUser, setToken, hasPermission,
      setMustChangePassword: (v) => setState(s => ({ ...s, mustChangePassword: v })),
      setTotpRequired: (v) => setState(s => ({ ...s, totpRequired: v })),
      setTotpSetupRequired: (v) => setState(s => ({ ...s, totpSetupRequired: v })),
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
