/**
 * 审计日志表格组件
 * AuditLogTable Component
 * T166: Create AuditLogTable component
 *
 * 展示系统审计日志，支持筛选和分页。
 */

import clsx from 'clsx';
import { AuditLog } from '../../services/adminService';

export interface AuditLogTableProps {
  logs: AuditLog[];
  loading?: boolean;
  onViewDetails?: (log: AuditLog) => void;
}

const actionColors: Record<string, string> = {
  login: 'bg-green-500/20 text-green-400',
  logout: 'bg-slate-500/20 text-slate-400',
  login_failed: 'bg-red-500/20 text-red-400',
  create: 'bg-cyan-500/20 text-cyan-400',
  update: 'bg-yellow-500/20 text-yellow-400',
  delete: 'bg-red-500/20 text-red-400',
  export: 'bg-purple-500/20 text-purple-400',
  config_change: 'bg-orange-500/20 text-orange-400',
};

const actionLabels: Record<string, string> = {
  login: '登录',
  logout: '登出',
  login_failed: '登录失败',
  register: '注册',
  create: '创建',
  read: '查看',
  update: '更新',
  delete: '删除',
  export: '导出',
  config_change: '配置变更',
  password_change: '密码修改',
  role_change: '角色变更',
  task_run: '运行任务',
  task_cancel: '取消任务',
};

export function AuditLogTable({
  logs,
  loading = false,
  onViewDetails,
}: AuditLogTableProps) {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <svg
          className="w-12 h-12 mx-auto mb-4 opacity-50"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p>暂无审计日志</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-700/50">
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
              时间
            </th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
              用户
            </th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
              操作
            </th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
              资源
            </th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
              IP 地址
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-slate-400">
              详情
            </th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr
              key={log.id}
              className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
            >
              <td className="px-4 py-3 text-sm text-slate-300 whitespace-nowrap">
                {formatDate(log.created_at)}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center text-xs text-slate-300">
                    {log.username?.charAt(0).toUpperCase() || '?'}
                  </div>
                  <span className="text-sm text-slate-200">
                    {log.username || log.user_id || '系统'}
                  </span>
                </div>
              </td>
              <td className="px-4 py-3">
                <span
                  className={clsx(
                    'px-2 py-1 text-xs rounded-full',
                    actionColors[log.action] || 'bg-slate-500/20 text-slate-400'
                  )}
                >
                  {actionLabels[log.action] || log.action}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-slate-300">
                {log.resource_type && (
                  <span className="text-slate-400">
                    {log.resource_type}
                    {log.resource_id && (
                      <span className="text-slate-500">:{log.resource_id}</span>
                    )}
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-sm text-slate-400 font-mono">
                {log.ip_address || '-'}
              </td>
              <td className="px-4 py-3 text-right">
                {log.details && Object.keys(log.details).length > 0 && onViewDetails && (
                  <button
                    onClick={() => onViewDetails(log)}
                    className="p-1.5 text-slate-400 hover:text-cyan-400 transition-colors"
                    title="查看详情"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AuditLogTable;
