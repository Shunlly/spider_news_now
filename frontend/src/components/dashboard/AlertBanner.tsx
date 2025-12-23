/**
 * 警报横幅组件
 * AlertBanner Component
 * T141: Create AlertBanner component
 *
 * 在 Dashboard 顶部显示系统警报和通知。
 */

import { useState } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import clsx from 'clsx';

export type AlertType = 'info' | 'success' | 'warning' | 'error';

export interface Alert {
  id: string;
  type: AlertType;
  title: string;
  message: string;
  timestamp: string;
  dismissible?: boolean;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export interface AlertBannerProps {
  alerts: Alert[];
  onDismiss?: (id: string) => void;
  maxVisible?: number;
  className?: string;
}

const alertConfig = {
  info: {
    icon: Info,
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    textColor: 'text-blue-400',
    iconColor: 'text-blue-400',
  },
  success: {
    icon: CheckCircle,
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/30',
    textColor: 'text-green-400',
    iconColor: 'text-green-400',
  },
  warning: {
    icon: AlertTriangle,
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
    textColor: 'text-yellow-400',
    iconColor: 'text-yellow-400',
  },
  error: {
    icon: AlertCircle,
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    textColor: 'text-red-400',
    iconColor: 'text-red-400',
  },
};

export function AlertBanner({
  alerts,
  onDismiss,
  maxVisible = 3,
  className,
}: AlertBannerProps) {
  const [expanded, setExpanded] = useState(false);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const visibleAlerts = alerts.filter((alert) => !dismissed.has(alert.id));
  const displayAlerts = expanded ? visibleAlerts : visibleAlerts.slice(0, maxVisible);
  const hiddenCount = visibleAlerts.length - maxVisible;

  const handleDismiss = (id: string) => {
    setDismissed((prev) => new Set(prev).add(id));
    onDismiss?.(id);
  };

  if (visibleAlerts.length === 0) return null;

  return (
    <div className={clsx('space-y-2', className)}>
      {displayAlerts.map((alert) => {
        const config = alertConfig[alert.type];
        const Icon = config.icon;

        return (
          <div
            key={alert.id}
            className={clsx(
              'rounded-lg border p-3 animate-fade-in',
              config.bgColor,
              config.borderColor
            )}
          >
            <div className="flex items-start gap-3">
              <Icon className={clsx('w-5 h-5 flex-shrink-0 mt-0.5', config.iconColor)} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className={clsx('font-medium text-sm', config.textColor)}>
                    {alert.title}
                  </h4>
                  <span className="text-xs text-slate-500">
                    {formatTime(alert.timestamp)}
                  </span>
                </div>
                <p className="text-sm text-slate-300 mt-0.5">{alert.message}</p>
                {alert.action && (
                  <button
                    onClick={alert.action.onClick}
                    className={clsx(
                      'text-sm mt-2 hover:underline',
                      config.textColor
                    )}
                  >
                    {alert.action.label} →
                  </button>
                )}
              </div>
              {alert.dismissible !== false && (
                <button
                  onClick={() => handleDismiss(alert.id)}
                  className="p-1 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        );
      })}

      {/* 展开/收起按钮 */}
      {hiddenCount > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-300 transition-colors"
        >
          {expanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              收起
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              还有 {hiddenCount} 条警报
            </>
          )}
        </button>
      )}
    </div>
  );
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return '刚刚';
  if (diffMin < 60) return `${diffMin}分钟前`;

  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour}小时前`;

  return date.toLocaleDateString('zh-CN');
}

export default AlertBanner;
