import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Globe, ArrowUp, ArrowDown, Clock, Zap, Activity, TrendingUp, Server } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import WelcomePopup from '../components/WelcomePopup';
import api from '../utils/api';

interface DashboardStats {
  total_websites: number;
  websites_up: number;
  websites_down: number;
  avg_latency: number | null;
  avg_page_load: number | null;
  uptime_percentage: number | null;
}

interface Website {
  id: number;
  name: string;
  url: string;
  is_active: boolean;
  latest_check: {
    is_up: boolean;
    latency_ms: number;
    page_load_time_ms: number;
    status_code: number;
    checked_at: string;
  } | null;
}

interface HistoryPoint {
  checked_at: string;
  latency_ms: number | null;
  page_load_time_ms: number | null;
}

export default function Dashboard() {
  const { user } = useAuth();
  const [showWelcome, setShowWelcome] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [websites, setWebsites] = useState<Website[]>([]);
  const [selectedSite, setSelectedSite] = useState<number | null>(null);
  const [chartData, setChartData] = useState<HistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const welcomed = sessionStorage.getItem('webpulse_welcomed');
    if (!welcomed) {
      setShowWelcome(true);
      sessionStorage.setItem('webpulse_welcomed', 'true');
    }

    Promise.all([
      api.get('/api/websites/dashboard'),
      api.get('/api/websites'),
    ]).then(([statsRes, sitesRes]) => {
      setStats(statsRes.data);
      setWebsites(sitesRes.data);
      if (sitesRes.data.length > 0) {
        setSelectedSite(sitesRes.data[0].id);
      }
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedSite) {
      api.get(`/api/websites/${selectedSite}/history?limit=24`).then(res => {
        setChartData(res.data.reverse().map((d: any) => ({
          checked_at: new Date(d.checked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          latency_ms: d.latency_ms,
          page_load_time_ms: d.page_load_time_ms,
        })));
      });
    }
  }, [selectedSite]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-3 border-pink-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const statCards = [
    { label: 'Total Sites', value: stats?.total_websites || 0, icon: Globe, color: 'text-pink-500', bg: 'bg-pink-500/10' },
    { label: 'Sites Up', value: stats?.websites_up || 0, icon: ArrowUp, color: 'text-green-400', bg: 'bg-green-500/10' },
    { label: 'Sites Down', value: stats?.websites_down || 0, icon: ArrowDown, color: 'text-red-400', bg: 'bg-red-500/10' },
    { label: 'Avg Latency', value: stats?.avg_latency ? `${stats.avg_latency.toFixed(0)}ms` : 'N/A', icon: Clock, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { label: 'Avg Load Time', value: stats?.avg_page_load ? `${stats.avg_page_load.toFixed(0)}ms` : 'N/A', icon: Zap, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
    { label: 'Uptime', value: stats?.uptime_percentage ? `${stats.uptime_percentage}%` : 'N/A', icon: Activity, color: 'text-purple-400', bg: 'bg-purple-500/10' },
  ];

  return (
    <div className="space-y-6">
      {showWelcome && user && <WelcomePopup username={user.username} onClose={() => setShowWelcome(false)} />}

      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Dashboard</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-secondary)' }}>Real-time monitoring overview</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((card) => (
          <div key={card.label} className="glass-card p-4">
            <div className={`w-10 h-10 rounded-xl ${card.bg} flex items-center justify-center mb-3`}>
              <card.icon className={`w-5 h-5 ${card.color}`} />
            </div>
            <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{card.value}</p>
            <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>{card.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}