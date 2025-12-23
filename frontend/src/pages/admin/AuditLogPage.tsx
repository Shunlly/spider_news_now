/**
 * 审计日志页面
 * AuditLogPage
 * T168: Implement AuditLogPage
 *
 * 提供系统审计日志的查看和筛选功能，仅管理员可访问。
 */

import { useState, useEffect, useCallback } from 'react';
import { HUDPanel, StoneButton, StoneInput, StoneSelect, StoneModal } from '@/components/ui';
import { TenantSelector, AuditLogTable } from '@/components/admin';
import {
  RefreshCw,
  FileText,
  Shield,
  Clock,
  Filter,
  Download,
} from 'lucide-react';
import {
  getAuditLogs,
  type AuditLog,
} from '@/services/adminService';

export default function AuditLogPage() {
  // 状态
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [tenantFilter, setTenantFilter] = useState<number | null>(null);
  const pageSize = 50;

  // 详情模态框状态
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  // 加载审计日志
  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      };
      if (search) params.search = search;
      if (actionFilter) params.action = actionFilter;
      if (tenantFilter) params.tenant_id = tenantFilter;

      const response = await getAuditLogs(params);
      setLogs(response.logs);
      setTotal(response.total);
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    } finally {
      setLoading(false);
    }
  }, [page, search, actionFilter, tenantFilter]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // 查看详情
  const handleViewDetails = (log: AuditLog) => {
    setSelectedLog(log);
    setShowDetailModal(true);
  };

  // 导出日志
  const handleExport = () => {
    const csvContent = [
      ['时间', '用户', '操作', '资源类型', '资源ID', 'IP地址'].join(','),
      ...logs.map((log) =>
        [
          log.created_at,
          log.username || log.user_id || '系统',
          log.action,
          log.resource_type || '',
          log.resource_id || '',
          log.ip_address || '',
        ].join(',')
      ),
    ].join('\n');

    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const totalPages = Math.ceil(total / pageSize);

  // 统计
  const todayCount = logs.filter((log) => {
    const today = new Date().toDateString();
    return new Date(log.created_at).toDateString() === today;
  }).length;

  const loginCount = logs.filter((log) => log.action === 'login').length;
  const sensitiveCount = logs.filter((log) =>
    ['delete', 'config_change', 'role_change', 'password_change'].includes(log.action)
  ).length;

  return (
    <div className="min-h-screen bg-slate-900 p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">审计日志</h1>
          <p className="text-sm text-slate-400 mt-1">查看系统操作记录和安全事件</p>
        </div>
        <div className="flex items-center gap-3">
          <TenantSelector
            value={tenantFilter}
            onChange={(id) => {
              setTenantFilter(id);
              setPage(1);
            }}
          />
          <StoneButton onClick={handleExport} disabled={logs.length === 0}>
            <Download className="w-4 h-4 mr-2" />
            导出
          </StoneButton>
          <StoneButton onClick={fetchLogs} disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </StoneButton>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          icon={<FileText className="w-5 h-5" />}
          label="当前页日志"
          value={logs.length}
          color="cyan"
        />
        <StatCard
          icon={<Clock className="w-5 h-5" />}
          label="今日记录"
          value={todayCount}
          color="green"
        />
        <StatCard
          icon={<Shield className="w-5 h-5" />}
          label="登录事件"
          value={loginCount}
          color="purple"
        />
        <StatCard
          icon={<Filter className="w-5 h-5" />}
          label="敏感操作"
          value={sensitiveCount}
          color="yellow"
        />
      </div>

      {/* 日志列表 */}
      <HUDPanel title="操作日志" className="p-0">
        <div className="p-4 border-b border-slate-700/50 flex flex-wrap items-center gap-4">
          <StoneInput
            placeholder="搜索用户或资源..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="max-w-xs"
          />
          <StoneSelect
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
            className="w-40"
          >
            <option value="">所有操作</option>
            <option value="login">登录</option>
            <option value="logout">登出</option>
            <option value="login_failed">登录失败</option>
            <option value="create">创建</option>
            <option value="update">更新</option>
            <option value="delete">删除</option>
            <option value="export">导出</option>
            <option value="config_change">配置变更</option>
            <option value="password_change">密码修改</option>
            <option value="role_change">角色变更</option>
            <option value="task_run">运行任务</option>
            <option value="task_cancel">取消任务</option>
          </StoneSelect>
        </div>

        <AuditLogTable
          logs={logs}
          loading={loading}
          onViewDetails={handleViewDetails}
        />

        {/* 分页 */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-700/50 flex items-center justify-between">
            <span className="text-sm text-slate-400">
              共 {total} 条，第 {page}/{totalPages} 页
            </span>
            <div className="flex items-center gap-2">
              <StoneButton
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                上一页
              </StoneButton>
              <StoneButton
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                下一页
              </StoneButton>
            </div>
          </div>
        )}
      </HUDPanel>

      {/* 详情模态框 */}
      <StoneModal
        open={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        title="日志详情"
      >
        {selectedLog && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">时间</label>
                <p className="text-slate-200">
                  {new Date(selectedLog.created_at).toLocaleString('zh-CN')}
                </p>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">用户</label>
                <p className="text-slate-200">
                  {selectedLog.username || selectedLog.user_id || '系统'}
                </p>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">操作</label>
                <p className="text-slate-200">{selectedLog.action}</p>
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">IP 地址</label>
                <p className="text-slate-200 font-mono">{selectedLog.ip_address || '-'}</p>
              </div>
              {selectedLog.resource_type && (
                <div>
                  <label className="block text-sm text-slate-400 mb-1">资源类型</label>
                  <p className="text-slate-200">{selectedLog.resource_type}</p>
                </div>
              )}
              {selectedLog.resource_id && (
                <div>
                  <label className="block text-sm text-slate-400 mb-1">资源 ID</label>
                  <p className="text-slate-200 font-mono">{selectedLog.resource_id}</p>
                </div>
              )}
            </div>

            {selectedLog.details && Object.keys(selectedLog.details).length > 0 && (
              <div>
                <label className="block text-sm text-slate-400 mb-1">详细信息</label>
                <pre className="bg-slate-800 rounded-lg p-3 text-sm text-slate-300 overflow-auto max-h-60">
                  {JSON.stringify(selectedLog.details, null, 2)}
                </pre>
              </div>
            )}

            <div className="flex justify-end pt-4">
              <StoneButton onClick={() => setShowDetailModal(false)}>关闭</StoneButton>
            </div>
          </div>
        )}
      </StoneModal>
    </div>
  );
}

// 统计卡片子组件
function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: 'cyan' | 'green' | 'purple' | 'yellow';
}) {
  const colorClasses = {
    cyan: 'text-cyan-400 bg-cyan-500/10',
    green: 'text-green-400 bg-green-500/10',
    purple: 'text-purple-400 bg-purple-500/10',
    yellow: 'text-yellow-400 bg-yellow-500/10',
  };

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700/50 p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${colorClasses[color]}`}>{icon}</div>
        <div>
          <div className="text-sm text-slate-400">{label}</div>
          <div className="text-2xl font-bold text-slate-200">{value}</div>
        </div>
      </div>
    </div>
  );
}
