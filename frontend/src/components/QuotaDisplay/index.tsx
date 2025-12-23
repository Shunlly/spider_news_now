/**
 * HUD 风格配额显示组件
 * HUD-style Quota Display Component
 *
 * 深色主题 + 发光效果
 */

import { useState, useEffect, useCallback } from 'react';
import { Zap, Clock, AlertTriangle, RefreshCw } from 'lucide-react';
import quotaService from '../../services/quotaService';
import type { QuotaInfo } from '../../types/auth';

interface QuotaDisplayProps {
  mode?: 'compact' | 'full';
  className?: string;
}

const tierColors: Record<string, string> = {
  free: 'bg-slate-500/20 text-slate-400 border border-slate-500/30',
  basic: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  pro: 'bg-purple-500/20 text-purple-400 border border-purple-500/30',
};

const tierNames: Record<string, string> = {
  free: 'FREE',
  basic: 'BASIC',
  pro: 'PRO',
};

const formatResetTime = (resetAt: string | null): string => {
  if (!resetAt) return '--';

  const reset = new Date(resetAt);
  const now = new Date();
  const diffMs = reset.getTime() - now.getTime();

  if (diffMs <= 0) return '即将重置';

  const hours = Math.floor(diffMs / (1000 * 60 * 60));
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
};

const QuotaDisplay: React.FC<QuotaDisplayProps> = ({
  mode = 'full',
  className = '',
}) => {
  const [quota, setQuota] = useState<QuotaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQuota = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await quotaService.getQuota();
      setQuota(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取配额信息失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQuota();
  }, [fetchQuota]);

  if (loading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-4 bg-slate-700/50 rounded w-3/4 mb-2"></div>
        <div className="h-2 bg-slate-700/50 rounded w-full"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-sm text-red-400 ${className}`}>
        {error}
        <button
          onClick={fetchQuota}
          className="ml-2 text-slate-500 hover:text-cyan-400"
        >
          <RefreshCw className="w-4 h-4 inline" />
        </button>
      </div>
    );
  }

  if (!quota) return null;

  const dailyPercent = quota.daily_limit > 0
    ? Math.round((quota.daily_used / quota.daily_limit) * 100)
    : 0;

  const getProgressColor = (percent: number, warning: boolean) => {
    if (warning || percent >= 90) return 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]';
    if (percent >= 70) return 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.5)]';
    return 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]';
  };

  if (mode === 'compact') {
    return (
      <div className={`p-3 bg-slate-800/30 border border-slate-700/50 rounded-lg ${className}`}>
        <div className="flex items-center gap-2 mb-2">
          <Zap className="w-4 h-4 text-cyan-400" />
          <span className="text-xs text-slate-400 font-mono">QUOTA</span>
          <span className="text-xs text-cyan-400 font-mono ml-auto">
            {quota.daily_remaining}/{quota.daily_limit}
          </span>
        </div>
        <div className="h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${getProgressColor(dailyPercent, quota.warning)}`}
            style={{ width: `${dailyPercent}%` }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className={`p-4 bg-slate-800/30 rounded-lg border border-slate-700/50 ${className}`}>
      {/* 标题行 */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-slate-300 flex items-center gap-2">
          <Zap className="w-4 h-4 text-cyan-400" />
          配额使用
        </h3>
        <span className={`px-2 py-0.5 text-xs rounded ${tierColors[quota.tier] || tierColors.free}`}>
          {tierNames[quota.tier] || quota.tier}
        </span>
      </div>

      {/* 警告提示 */}
      {quota.warning && (
        <div className="mb-3 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0" />
          <span className="text-xs text-yellow-400">配额即将用尽，请注意使用</span>
        </div>
      )}

      {/* 每日配额 */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-slate-500 font-mono text-xs">DAILY</span>
          <span className="text-slate-300 font-mono text-xs">
            {quota.daily_used} / {quota.daily_limit}
          </span>
        </div>
        <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${getProgressColor(dailyPercent, quota.warning)}`}
            style={{ width: `${dailyPercent}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-1">
          <span className="text-xs text-slate-500 font-mono">剩余 {quota.daily_remaining}</span>
          <span className="text-xs text-cyan-400 font-mono">{dailyPercent}%</span>
        </div>
      </div>

      {/* 并发任务 */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-slate-500 font-mono text-xs">CONCURRENT</span>
          <span className="text-slate-300 font-mono text-xs">
            {quota.concurrent_used} / {quota.concurrent_limit}
          </span>
        </div>
        <div className="flex gap-1">
          {Array.from({ length: quota.concurrent_limit }).map((_, i) => (
            <div
              key={i}
              className={`flex-1 h-2 rounded-full ${
                i < quota.concurrent_used
                  ? 'bg-blue-500 shadow-[0_0_6px_rgba(59,130,246,0.5)]'
                  : 'bg-slate-700/50'
              }`}
            />
          ))}
        </div>
      </div>

      {/* 重置时间 */}
      <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
        <Clock className="w-3 h-3" />
        <span>RESET: {formatResetTime(quota.reset_at)}</span>
      </div>
    </div>
  );
};

export default QuotaDisplay;
