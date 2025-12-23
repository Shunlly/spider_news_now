/**
 * 配额警告组件
 * QuotaWarning Component
 * T131: Create QuotaWarning component
 *
 * 当用户配额接近或已达到限制时显示警告。
 */

import { AlertTriangle, AlertCircle, Info } from 'lucide-react';
import clsx from 'clsx';
import type { QuotaInfo } from '@/types/auth';

export interface QuotaWarningProps {
  quota: QuotaInfo | null;
  className?: string;
  showDetails?: boolean;
}

type WarningLevel = 'none' | 'info' | 'warning' | 'critical';

function getWarningLevel(quota: QuotaInfo): WarningLevel {
  const dailyPercent = (quota.daily_used / quota.daily_limit) * 100;
  const concurrentPercent = (quota.concurrent_used / quota.concurrent_limit) * 100;

  // 已用完
  if (quota.daily_remaining <= 0 || quota.concurrent_remaining <= 0) {
    return 'critical';
  }

  // 超过 90%
  if (dailyPercent >= 90 || concurrentPercent >= 90) {
    return 'warning';
  }

  // 超过 75%
  if (dailyPercent >= 75 || concurrentPercent >= 75) {
    return 'info';
  }

  return 'none';
}

const warningConfig = {
  none: null,
  info: {
    icon: Info,
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    textColor: 'text-blue-400',
    title: '配额提醒',
    getMessage: (quota: QuotaInfo) =>
      `今日已使用 ${quota.daily_used}/${quota.daily_limit} 次采集配额`,
  },
  warning: {
    icon: AlertTriangle,
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
    textColor: 'text-yellow-400',
    title: '配额警告',
    getMessage: (quota: QuotaInfo) =>
      `配额即将用完！今日剩余 ${quota.daily_remaining} 次`,
  },
  critical: {
    icon: AlertCircle,
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    textColor: 'text-red-400',
    title: '配额已用完',
    getMessage: (quota: QuotaInfo) =>
      quota.daily_remaining <= 0
        ? `今日配额已用完，将于 ${formatResetTime(quota.reset_at)} 重置`
        : `并发任务数已达上限 (${quota.concurrent_limit})`,
  },
};

function formatResetTime(resetAt: string | null): string {
  if (!resetAt) return '明日';
  const date = new Date(resetAt);
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

export function QuotaWarning({ quota, className, showDetails = false }: QuotaWarningProps) {
  if (!quota) return null;

  const level = getWarningLevel(quota);
  if (level === 'none') return null;

  const config = warningConfig[level];
  if (!config) return null;

  const Icon = config.icon;

  return (
    <div
      className={clsx(
        'rounded-lg border p-4',
        config.bgColor,
        config.borderColor,
        className
      )}
    >
      <div className="flex items-start gap-3">
        <Icon className={clsx('w-5 h-5 flex-shrink-0 mt-0.5', config.textColor)} />
        <div className="flex-1 min-w-0">
          <h4 className={clsx('font-medium', config.textColor)}>{config.title}</h4>
          <p className="text-sm text-slate-300 mt-1">{config.getMessage(quota)}</p>

          {showDetails && (
            <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-slate-400">每日配额</div>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={clsx(
                        'h-full rounded-full transition-all',
                        quota.daily_remaining <= 0 ? 'bg-red-500' :
                        quota.daily_used / quota.daily_limit >= 0.9 ? 'bg-yellow-500' :
                        'bg-cyan-500'
                      )}
                      style={{ width: `${Math.min((quota.daily_used / quota.daily_limit) * 100, 100)}%` }}
                    />
                  </div>
                  <span className="text-slate-300 whitespace-nowrap">
                    {quota.daily_used}/{quota.daily_limit}
                  </span>
                </div>
              </div>
              <div>
                <div className="text-slate-400">并发任务</div>
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={clsx(
                        'h-full rounded-full transition-all',
                        quota.concurrent_remaining <= 0 ? 'bg-red-500' :
                        quota.concurrent_used / quota.concurrent_limit >= 0.9 ? 'bg-yellow-500' :
                        'bg-green-500'
                      )}
                      style={{ width: `${Math.min((quota.concurrent_used / quota.concurrent_limit) * 100, 100)}%` }}
                    />
                  </div>
                  <span className="text-slate-300 whitespace-nowrap">
                    {quota.concurrent_used}/{quota.concurrent_limit}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default QuotaWarning;
