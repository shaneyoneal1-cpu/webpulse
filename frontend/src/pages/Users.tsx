import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Users as UsersIcon, Plus, Shield, Trash2, Check, X } from 'lucide-react';
import api from '../utils/api';

export default function Users() {
  const { user: currentUser, hasPermission } = useAuth();
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadUsers = () => {
    api.get('/api/admin/users').then(res => setUsers(res.data)).finally(() => setLoading(false));
  };

  useEffect(() => { loadUsers(); }, []);

  if (loading) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Team Management</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Manage sub-admin accounts and permissions</p>
        </div>
      </div>

      <div className="grid gap-4">
        {users.map(u => (
          <div key={u.id} className="glass-card p-5 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-pink-500/10 flex items-center justify-center text-pink-500 font-bold">
                {u.username[0].toUpperCase()}
              </div>
              <div>
                <h3 className="font-semibold" style={{ color: 'var(--text-primary)' }}>{u.username}</h3>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {u.is_main_admin ? 'Main Admin' : 'Sub-Admin'}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
