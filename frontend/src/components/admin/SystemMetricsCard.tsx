/**
 * 系统指标卡片组件
 * SystemMetricsCard Component
 * T167: Create SystemMetricsCard component
 *
 * 展示系统运行指标，包括任务队列、处理速率和资源使用。
 */

import clsx from 'clsx';
import { SystemMetrics } from '../../services/adminService';

export interface SystemMetricsCardProps {
  metrics: SystemMetrics | null;
  loading?: boolean;
  className?: string;
}

export function SystemMetricsCard({
  metrics,
  loading = false,
  className,
}: SystemMetricsCardProps) {
  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
      return `${days}天 ${hours}小时`;
    }
    if (hours > 0) {
      return `${hours}小时 ${minutes}分钟`;
    }
    return `${minutes}分钟`;
  };

  if (loading) {
    return (
      <div className={clsx('bg-slate-800/50 rounded-lg border border-slate-700/50 p-6', className)}>
        <div className="flex items-center justify-center py-8">
          <div className="w-8 h-8 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className={clsx('bg-slate-800/50 rounded-lg border border-slate-700/50 p-6', className)}>
        <div className="text-center py-8 text-slate-400">
          无法获取系统指标
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('space-y-6', className)}>
      {/* 系统状态概览 */}
      <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-slate-200">系统状态</h3>
          <span className="text-sm text-slate-400">
            运行时间: {formatUptime(metrics.uptime_seconds)}
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricItem
            label="活跃爬虫"
            value={metrics.resources.active_scrapers}
            total={metrics.resources.total_scrapers}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
            }
            color="cyan"
          />
          <MetricItem
            label="WebSocket 连接"
            value={metrics.resources.active_connections}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
              </svg>
            }
            color="green"
          />
          <MetricItem
            label="内存使用"
            value={`${metrics.resources.memory_usage_mb.toFixed(1)} MB`}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            }
            color="purple"
          />
          <MetricItem
            label="数据库连接"
            value={metrics.resources.db_connections}
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
              </svg>
            }
            color="yellow"
          />
        </div>
      </div>

      {/* 任务队列 */}
      <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-6">
        <h3 className="text-lg font-medium text-slate-200 mb-4">任务队列</h3>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <QueueItem label="等待中" value={metrics.task_queue.pending} color="yellow" />
          <QueueItem label="运行中" value={metrics.task_queue.running} color="cyan" />
          <QueueItem label="已完成" value={metrics.task_queue.completed} color="green" />
          <QueueItem label="失败" value={metrics.task_queue.failed} color="red" />
          <QueueItem label="总计" value={metrics.task_queue.total} color="slate" />
        </div>

        {/* 进度条 */}
        <div className="mt-4">
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden flex">
            {metrics.task_queue.total > 0 && (
              <>
                <div
                  className="bg-green-500 h-full"
                  style={{
                    width: `${(metrics.task_queue.completed / metrics.task_queue.total) * 100}%`,
                  }}
                />
                <div
                  className="bg-cyan-500 h-full"
                  style={{
                    width: `${(metrics.task_queue.running / metrics.task_queue.total) * 100}%`,
                  }}
                />
                <div
                  className="bg-yellow-500 h-full"
                  style={{
                    width: `${(metrics.task_queue.pending / metrics.task_queue.total) * 100}%`,
                  }}
                />
                <div
                  className="bg-red-500 h-full"
                  style={{
                    width: `${(metrics.task_queue.failed / metrics.task_queue.total) * 100}%`,
                  }}
                />
              </>
            )}
          </div>
        </div>
      </div>

      {/* 处理速率 */}
      <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-6">
        <h3 className="text-lg font-medium text-slate-200 mb-4">处理速率</h3>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          <RateItem
            label="文章采集"
            perMinute={metrics.processing_rate.articles_per_minute}
            perHour={metrics.processing_rate.articles_per_hour}
            unit="篇"
          />
          <RateItem
            label="任务完成"
            perMinute={metrics.processing_rate.tasks_per_minute}
            perHour={metrics.processing_rate.tasks_per_hour}
            unit="个"
          />
          <div>
            <div className="text-sm text-slate-400 mb-1">平均任务时长</div>
            <div className="text-2xl font-medium text-slate-200">
              {metrics.processing_rate.avg_task_duration_seconds.toFixed(1)}
              <span className="text-sm text-slate-400 ml-1">秒</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// 子组件

interface MetricItemProps {
  label: string;
  value: number | string;
  total?: number;
  icon: React.ReactNode;
  color: 'cyan' | 'green' | 'purple' | 'yellow' | 'red' | 'slate';
}

function MetricItem({ label, value, total, icon, color }: MetricItemProps) {
  const colorClasses = {
    cyan: 'text-cyan-400 bg-cyan-500/10',
    green: 'text-green-400 bg-green-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
    yellow: 'text-yellow-400 bg-yellow-500/10',
    red: 'text-red-400 bg-red-500/10',
    slate: 'text-slate-400 bg-slate-500/10',
  };

  return (
    <div className="flex items-center gap-3">
      <div className={clsx('p-2 rounded-lg', colorClasses[color])}>
        {icon}
      </div>
      <div>
        <div className="text-sm text-slate-400">{label}</div>
        <div className="text-lg font-medium text-slate-200">
          {value}
          {total !== undefined && (
            <span className="text-sm text-slate-500">/{total}</span>
          )}
        </div>
      </div>
    </div>
  );
}

interface QueueItemProps {
  label: string;
  value: number;
  color: 'cyan' | 'green' | 'yellow' | 'red' | 'slate';
}

function QueueItem({ label, value, color }: QueueItemProps) {
  const colorClasses = {
    cyan: 'text-cyan-400',
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
    slate: 'text-slate-400',
  };

  return (
    <div className="text-center">
      <div className={clsx('text-2xl font-medium', colorClasses[color])}>
        {value}
      </div>
      <div className="text-sm text-slate-400">{label}</div>
    </div>
  );
}

interface RateItemProps {
  label: string;
  perMinute: number;
  perHour: number;
  unit: string;
}

function RateItem({ label, perMinute, perHour, unit }: RateItemProps) {
  return (
    <div>
      <div className="text-sm text-slate-400 mb-1">{label}</div>
      <div className="text-2xl font-medium text-slate-200">
        {perMinute.toFixed(1)}
        <span className="text-sm text-slate-400 ml-1">{unit}/分钟</span>
      </div>
      <div className="text-sm text-slate-500">
        {perHour.toFixed(0)} {unit}/小时
      </div>
    </div>
  );
}

export default SystemMetricsCard;
