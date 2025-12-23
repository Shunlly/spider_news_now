/**
 * 系统监控页面
 * SystemMonitorPage
 * T169: Implement SystemMonitorPage
 *
 * 提供系统资源监控和健康状态查看，仅管理员可访问。
 */

import { useState, useEffect, useCallback } from 'react';
import { HUDPanel, StoneButton } from '@/components/ui';
import { SystemMetricsCard } from '@/components/admin';
import {
  RefreshCw,
  Activity,
  Server,
  Database,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Zap,
} from 'lucide-react';
import {
  getSystemMetrics,
  getHealthStatus,
  type SystemMetrics,
  type HealthStatus,
} from '@/services/adminService';

export default function SystemMonitorPage() {
  // 状态
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // 加载数据
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [metricsData, healthData] = await Promise.all([
        getSystemMetrics(),
        getHealthStatus(),
      ]);
      setMetrics(metricsData);
      setHealth(healthData);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch system data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchData, 30000); // 30秒刷新
    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  // 整体健康状态
  const overallStatus = health
    ? health.services && Object.keys(health.services).length > 0
      ? Object.values(health.services).every((s) => s.status === 'healthy')
        ? 'healthy'
        : Object.values(health.services).some((s) => s.status === 'unhealthy')
        ? 'unhealthy'
        : 'degraded'
      : health.status || 'healthy'
    : 'unknown';

  const statusConfig = {
    healthy: { icon: CheckCircle, color: 'text-green-400', label: '健康' },
    degraded: { icon: AlertTriangle, color: 'text-yellow-400', label: '降级' },
    unhealthy: { icon: XCircle, color: 'text-red-400', label: '异常' },
    unknown: { icon: Activity, color: 'text-slate-400', label: '未知' },
  };

  const StatusIcon = statusConfig[overallStatus].icon;

  return (
    <div className="min-h-screen bg-slate-900 p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">系统监控</h1>
          <p className="text-sm text-slate-400 mt-1">
            实时监控系统资源和服务健康状态
            {lastUpdate && (
              <span className="ml-2 text-slate-500">
                最后更新: {lastUpdate.toLocaleTimeString('zh-CN')}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
            />
            自动刷新
          </label>
          <StoneButton onClick={fetchData} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </StoneButton>
        </div>
      </div>

      {/* 整体状态 */}
      <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div
              className={`p-3 rounded-xl ${
                overallStatus === 'healthy'
                  ? 'bg-green-500/10'
                  : overallStatus === 'degraded'
                  ? 'bg-yellow-500/10'
                  : 'bg-red-500/10'
              }`}
            >
              <StatusIcon className={`w-8 h-8 ${statusConfig[overallStatus].color}`} />
            </div>
            <div>
              <h2 className="text-xl font-medium text-slate-200">
                系统状态: {statusConfig[overallStatus].label}
              </h2>
              <p className="text-sm text-slate-400 mt-1">
                {health
                  ? health.services && Object.keys(health.services).length > 0
                    ? `${Object.values(health.services).filter((s) => s.status === 'healthy').length}/${
                        Object.keys(health.services).length
                      } 服务运行正常`
                    : `系统状态: ${health.status || '正常'}`
                  : '正在检测服务状态...'}
              </p>
            </div>
          </div>

          {metrics && (
            <div className="text-right">
              <div className="text-sm text-slate-400">运行时间</div>
              <div className="text-xl font-medium text-slate-200">
                {formatUptime(metrics.uptime_seconds)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 服务健康状态 */}
      <HUDPanel title="服务健康状态">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4">
          {health && health.services && Object.keys(health.services).length > 0 ? (
            Object.entries(health.services).map(([name, service]) => (
              <ServiceCard
                key={name}
                name={name}
                status={service.status}
                latency={service.latency_ms}
                message={service.message}
              />
            ))
          ) : health ? (
            <div className="col-span-full text-center py-8 text-slate-400">
              <Server className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>系统运行正常</p>
              <p className="text-sm mt-1">状态: {health.status}</p>
            </div>
          ) : (
            <>
              <ServiceCardSkeleton />
              <ServiceCardSkeleton />
              <ServiceCardSkeleton />
              <ServiceCardSkeleton />
            </>
          )}
        </div>
      </HUDPanel>

      {/* 系统指标 */}
      <HUDPanel title="系统指标">
        <div className="p-4">
          <SystemMetricsCard metrics={metrics} loading={loading} />
        </div>
      </HUDPanel>

      {/* 快速操作 */}
      <HUDPanel title="快速操作">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4">
          <QuickAction
            icon={<Zap className="w-5 h-5" />}
            label="清理缓存"
            description="清理系统缓存以释放内存"
            onClick={() => alert('功能开发中...')}
          />
          <QuickAction
            icon={<Database className="w-5 h-5" />}
            label="数据库优化"
            description="优化数据库查询和索引"
            onClick={() => alert('功能开发中...')}
          />
          <QuickAction
            icon={<Server className="w-5 h-5" />}
            label="重启服务"
            description="重启采集任务队列服务"
            onClick={() => alert('功能开发中...')}
            variant="danger"
          />
        </div>
      </HUDPanel>
    </div>
  );
}

// 格式化运行时间
function formatUptime(seconds: number): string {
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
}

// 服务卡片
function ServiceCard({
  name,
  status,
  latency,
  message,
}: {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  latency?: number;
  message?: string;
}) {
  const serviceNames: Record<string, string> = {
    database: '数据库',
    redis: 'Redis 缓存',
    meilisearch: '搜索引擎',
    minio: '对象存储',
    celery: '任务队列',
  };

  const statusColors = {
    healthy: 'border-green-500/50 bg-green-500/5',
    degraded: 'border-yellow-500/50 bg-yellow-500/5',
    unhealthy: 'border-red-500/50 bg-red-500/5',
  };

  const statusIcons = {
    healthy: <CheckCircle className="w-5 h-5 text-green-400" />,
    degraded: <AlertTriangle className="w-5 h-5 text-yellow-400" />,
    unhealthy: <XCircle className="w-5 h-5 text-red-400" />,
  };

  return (
    <div className={`rounded-lg border p-4 ${statusColors[status]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-slate-200">{serviceNames[name] || name}</span>
        {statusIcons[status]}
      </div>
      <div className="text-sm text-slate-400">
        {latency !== undefined && <span>延迟: {latency.toFixed(1)}ms</span>}
        {message && <p className="mt-1 text-xs">{message}</p>}
      </div>
    </div>
  );
}

// 服务卡片骨架屏
function ServiceCardSkeleton() {
  return (
    <div className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4 animate-pulse">
      <div className="flex items-center justify-between mb-2">
        <div className="h-5 w-20 bg-slate-700 rounded" />
        <div className="h-5 w-5 bg-slate-700 rounded-full" />
      </div>
      <div className="h-4 w-16 bg-slate-700 rounded" />
    </div>
  );
}

// 快速操作卡片
function QuickAction({
  icon,
  label,
  description,
  onClick,
  variant = 'default',
}: {
  icon: React.ReactNode;
  label: string;
  description: string;
  onClick: () => void;
  variant?: 'default' | 'danger';
}) {
  return (
    <button
      onClick={onClick}
      className={`text-left p-4 rounded-lg border transition-colors ${
        variant === 'danger'
          ? 'border-red-500/30 hover:border-red-500/50 hover:bg-red-500/5'
          : 'border-slate-700/50 hover:border-cyan-500/50 hover:bg-cyan-500/5'
      }`}
    >
      <div className="flex items-center gap-3 mb-2">
        <div
          className={`p-2 rounded-lg ${
            variant === 'danger' ? 'bg-red-500/10 text-red-400' : 'bg-cyan-500/10 text-cyan-400'
          }`}
        >
          {icon}
        </div>
        <span className="font-medium text-slate-200">{label}</span>
      </div>
      <p className="text-sm text-slate-400">{description}</p>
    </button>
  );
}
