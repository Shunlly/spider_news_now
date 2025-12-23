/**
 * 用户表格组件
 * UserTable Component
 * T117: Create UserTable component
 *
 * 展示用户列表，支持搜索、分页和操作。
 */

import { useState } from 'react';
import clsx from 'clsx';

export interface User {
  id: string;
  username: string;
  email: string;
  role_id: number;
  tenant_id: number | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface UserTableProps {
  users: User[];
  loading?: boolean;
  onEdit?: (user: User) => void;
  onDelete?: (user: User) => void;
  onToggleActive?: (user: User) => void;
  onResetPassword?: (user: User) => void;
}

const roleNames: Record<number, string> = {
  1: '超级管理员',
  2: '租户管理员',
  3: '普通用户',
};

const roleBadgeColors: Record<number, string> = {
  1: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  2: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  3: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
};

export function UserTable({
  users,
  loading = false,
  onEdit,
  onDelete,
  onToggleActive,
  onResetPassword,
}: UserTableProps) {
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set());

  const toggleSelect = (userId: string) => {
    const newSelected = new Set(selectedUsers);
    if (newSelected.has(userId)) {
      newSelected.delete(userId);
    } else {
      newSelected.add(userId);
    }
    setSelectedUsers(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedUsers.size === users.length) {
      setSelectedUsers(new Set());
    } else {
      setSelectedUsers(new Set(users.map((u) => u.id)));
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-8 h-8 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (users.length === 0) {
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
            d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
        <p>暂无用户数据</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-700/50">
            <th className="px-4 py-3 text-left">
              <input
                type="checkbox"
                checked={selectedUsers.size === users.length && users.length > 0}
                onChange={toggleSelectAll}
                className="rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500/30"
              />
            </th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
              用户名
            </th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
              邮箱
            </th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
              角色
            </th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
              状态
            </th>
            <th className="px-4 py-3 text-left text-sm font-medium text-slate-400">
              最后登录
            </th>
            <th className="px-4 py-3 text-right text-sm font-medium text-slate-400">
              操作
            </th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr
              key={user.id}
              className={clsx(
                'border-b border-slate-800/50 transition-colors',
                'hover:bg-slate-800/30',
                selectedUsers.has(user.id) && 'bg-cyan-500/5'
              )}
            >
              <td className="px-4 py-3">
                <input
                  type="checkbox"
                  checked={selectedUsers.has(user.id)}
                  onChange={() => toggleSelect(user.id)}
                  className="rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500/30"
                />
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-sm text-slate-300">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                  <span className="text-slate-200">{user.username}</span>
                </div>
              </td>
              <td className="px-4 py-3 text-slate-300">
                <div className="flex items-center gap-1">
                  {user.email}
                  {user.is_verified && (
                    <svg
                      className="w-4 h-4 text-green-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
              </td>
              <td className="px-4 py-3">
                <span
                  className={clsx(
                    'px-2 py-1 text-xs rounded-full border',
                    roleBadgeColors[user.role_id] || roleBadgeColors[3]
                  )}
                >
                  {roleNames[user.role_id] || '未知'}
                </span>
              </td>
              <td className="px-4 py-3">
                <span
                  className={clsx(
                    'px-2 py-1 text-xs rounded-full',
                    user.is_active
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-red-500/20 text-red-400'
                  )}
                >
                  {user.is_active ? '正常' : '已禁用'}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-slate-400">
                {formatDate(user.last_login_at)}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center justify-end gap-1">
                  {onEdit && (
                    <button
                      onClick={() => onEdit(user)}
                      className="p-1.5 text-slate-400 hover:text-cyan-400 transition-colors"
                      title="编辑"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                  )}
                  {onResetPassword && (
                    <button
                      onClick={() => onResetPassword(user)}
                      className="p-1.5 text-slate-400 hover:text-yellow-400 transition-colors"
                      title="重置密码"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                      </svg>
                    </button>
                  )}
                  {onToggleActive && (
                    <button
                      onClick={() => onToggleActive(user)}
                      className={clsx(
                        'p-1.5 transition-colors',
                        user.is_active
                          ? 'text-slate-400 hover:text-orange-400'
                          : 'text-slate-400 hover:text-green-400'
                      )}
                      title={user.is_active ? '禁用' : '启用'}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        {user.is_active ? (
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                        ) : (
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        )}
                      </svg>
                    </button>
                  )}
                  {onDelete && user.role_id !== 1 && (
                    <button
                      onClick={() => onDelete(user)}
                      className="p-1.5 text-slate-400 hover:text-red-400 transition-colors"
                      title="删除"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default UserTable;
