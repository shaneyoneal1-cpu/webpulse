import { useState, useEffect } from 'react';
import { X, TrendingUp, TrendingDown, Zap, Award, AlertCircle } from 'lucide-react';
import api from '../utils/api';

interface WeeklyRoundup {
  avg_latency_change: number | null;
  avg_speed_change: number | null;
  uptime_percentage: number | null;
  total_checks: number;
  sites_improved: number;
  sites_degraded: number;
  tip: string;
}

export default function WelcomePopup({ username, onClose }: { username: string; onClose: () => void }) {
  const [roundup, setRoundup] = useState<WeeklyRoundup | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/api/websites/weekly-roundup')
      .then(res => setRoundup(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass-card max-w-lg w-full p-8 slide-in relative">
        <button onClick={onClose} className="absolute top-4 right-4 p-2 rounded-lg hover:bg-pink-500/10 transition"
          style={{ color: 'var(--text-secondary)' }}>
          <X className="w-5 h-5" />
        </button>

        <div className="text-center mb-6">
          <div className="w-16 h-16 rounded-2xl gradient-pink flex items-center justify-center mx-auto mb-4">
            <Award className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
            Welcome back, {username}! 👋
          </h2>
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Here's your weekly roundup</p>
        </div>

        {loading ? (
          <div className="text-center py-8">
            <div className="w-8 h-8 border-2 border-pink-500 border-t-transparent rounded-full animate-spin mx-auto" />
          </div>
        ) : roundup ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl p-4" style={{ background: 'var(--bg-secondary)' }}>
                <div className="flex items-center gap-2 mb-1">
                  {roundup.avg_speed_change !== null && roundup.avg_speed_change < 0 ? (
                    <TrendingUp className="w-4 h-4 text-green-400" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-400" />
                  )}
                  <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Page Speed</span>
                </div>
                <p className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                  {roundup.avg_speed_change !== null
                    ? `${roundup.avg_speed_change > 0 ? '+' : ''}${roundup.avg_speed_change.toFixed(0)}ms`
                    : 'N/A'}
                </p>
              </div>
              <div className="rounded-xl p-4" style={{ background: 'var(--bg-secondary)' }}>
                <div className="flex items-center gap-2 mb-1">
                  <Zap className="w-4 h-4 text-yellow-400" />
                  <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Uptime</span>
                </div>
                <p className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                  {roundup.uptime_percentage !== null ? `${roundup.uptime_percentage}%` : 'N/A'}
                </p>
              </div>
              <div className="rounded-xl p-4" style={{ background: 'var(--bg-secondary)' }}>
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="w-4 h-4 text-green-400" />
                  <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Improved</span>
                </div>
                <p className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{roundup.sites_improved} sites</p>
              </div>
              <div className="rounded-xl p-4" style={{ background: 'var(--bg-secondary)' }}>
                <div className="flex items-center gap-2 mb-1">
                  <AlertCircle className="w-4 h-4 text-orange-400" />
                  <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>Total Checks</span>
                </div>
                <p className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{roundup.total_checks}</p>
              </div>
            </div>

            <div className="rounded-xl p-4 gradient-pink-subtle border border-pink-500/20">
              <div className="flex items-start gap-3">
                <Zap className="w-5 h-5 text-pink-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-pink-500 mb-1">💡 Performance Tip</p>
                  <p className="text-sm" style={{ color: 'var(--text-primary)' }}>{roundup.tip}</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <p style={{ color: 'var(--text-secondary)' }}>Start monitoring websites to see your weekly stats!</p>
          </div>
        )}

        <button onClick={onClose}
          className="w-full mt-6 gradient-pink text-white py-3 rounded-xl font-semibold hover:shadow-lg hover:shadow-pink-500/25 transition-all">
          Let's Go! 🚀
        </button>
      </div>
    </div>
  );
}
