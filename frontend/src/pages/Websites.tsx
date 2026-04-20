import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  Globe, Plus, Trash2, RefreshCw, ChevronDown, ChevronUp,
  AlertTriangle, CheckCircle, Clock, Zap, FileText, X
} from 'lucide-react';
import api from '../utils/api';

export default function Websites() {
  const { hasPermission } = useAuth();
  const [websites, setWebsites] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState('');
  const [newUrl, setNewUrl] = useState('');
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<number | null>(null);
  const [history, setHistory] = useState<Record<number, any[]>>({});
  const [checking, setChecking] = useState<number | null>(null);

  const loadWebsites = () => {
    api.get('/api/websites').then(res => setWebsites(res.data)).finally(() => setLoading(false));
  };

  useEffect(() => { loadWebsites(); }, []);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdding(true);
    setError('');
    try {
      await api.post('/api/websites', { name: newName, url: newUrl });
      setNewName('');
      setNewUrl('');
      setShowAdd(false);
      loadWebsites();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add');
    } finally {
      setAdding(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this website?')) return;
    await api.delete(`/api/websites/${id}`);
    loadWebsites();
  };

  const handleCheck = async (id: number) => {
    setChecking(id);
    try {
      await api.post(`/api/websites/${id}/check`);
      loadWebsites();
      if (expanded === id) {
        const histRes = await api.get(`/api/websites/${id}/history?limit=20`);
        setHistory(h => ({ ...h, [id]: histRes.data }));
      }
    } catch {} finally {
      setChecking(null);
    }
  };

  const toggleExpand = async (id: number) => {
    if (expanded === id) {
      setExpanded(null);
      return;
    }
    setExpanded(id);
    if (!history[id]) {
      const res = await api.get(`/api/websites/${id}/history?limit=20`);
      setHistory(h => ({ ...h, [id]: res.data }));
    }
  };

  if (loading) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Websites</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Manage your monitored targets</p>
        </div>
        {hasPermission('manage_websites') && (
          <button onClick={() => setShowAdd(true)}
            className="gradient-pink text-white px-5 py-2.5 rounded-xl font-medium flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add Website
          </button>
        )}
      </div>

      <div className="space-y-3">
        {websites.map(w => (
          <div key={w.id} className="glass-card">
            <div className="p-5 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <Globe className="w-5 h-5 text-pink-500" />
                <div>
                  <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>{w.name}</h3>
                  <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{w.url}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button onClick={() => handleCheck(w.id)} disabled={checking === w.id}
                  className="p-2 rounded-lg hover:bg-pink-500/10 text-pink-500 transition">
                  <RefreshCw className={`w-4 h-4 ${checking === w.id ? 'animate-spin' : ''}`} />
                </button>
                {hasPermission('manage_websites') && (
                  <button onClick={() => handleDelete(w.id)}
                    className="p-2 rounded-lg hover:bg-red-500/10 text-red-400 transition">
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
                <button onClick={() => toggleExpand(w.id)}
                  className="p-2 rounded-lg hover:bg-gray-500/10 transition" style={{ color: 'var(--text-secondary)' }}>
                  {expanded === w.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
