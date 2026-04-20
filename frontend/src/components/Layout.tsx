import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

import {
  Activity, Globe, Users, LogOut, Menu,
  Sun, Moon, LayoutDashboard, Shield
} from 'lucide-react';

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout, hasPermission } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', show: true },
    { path: '/websites', icon: Globe, label: 'Websites', show: hasPermission('view_websites') },
    { path: '/users', icon: Users, label: 'Users', show: hasPermission('view_users') },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg-primary)' }}>
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
        style={{ background: 'var(--bg-secondary)', borderRight: '1px solid var(--border-color)' }}>
        <div className="flex flex-col h-full">
          <div className="p-6 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl gradient-pink flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>WebPulse</h1>
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>Monitoring</p>
            </div>
          </div>

          <nav className="flex-1 px-4 space-y-1">
            {navItems.filter(i => i.show).map(item => (
              <Link key={item.path} to={item.path}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  isActive(item.path)
                    ? 'gradient-pink text-white shadow-lg shadow-pink-500/25'
                    : 'hover:bg-pink-500/10'
                }`}
                style={!isActive(item.path) ? { color: 'var(--text-secondary)' } : {}}>
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            ))}
          </nav>

          <div className="p-4 space-y-2">
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>
              <div className="w-8 h-8 rounded-lg gradient-pink flex items-center justify-center">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>{user?.username}</p>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {user?.is_main_admin ? 'Main Admin' : 'Sub-Admin'}
                </p>
              </div>
            </div>
            <button onClick={handleLogout}
              className="flex items-center gap-3 w-full px-4 py-3 rounded-xl transition-all hover:bg-red-500/10 text-red-400">
              <LogOut className="w-5 h-5" />
              <span className="font-medium">Logout</span>
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-h-screen">
        <header className="sticky top-0 z-30 px-4 lg:px-8 py-4 flex items-center justify-between"
          style={{ background: 'var(--bg-primary)', borderBottom: '1px solid var(--border-color)' }}>
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden p-2 rounded-lg" style={{ color: 'var(--text-primary)' }}>
            <Menu className="w-6 h-6" />
          </button>
          <div className="flex-1" />
          <button onClick={toggleTheme}
            className="p-2.5 rounded-xl transition-all hover:bg-pink-500/10"
            style={{ color: 'var(--text-secondary)' }}>
            {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </header>

        <main className="flex-1 p-4 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
