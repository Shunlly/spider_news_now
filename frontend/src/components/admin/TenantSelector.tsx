/**
 * 租户选择器组件
 * TenantSelector Component
 * T116: Create TenantSelector component
 *
 * 用于超级管理员切换租户视图。
 */

import { useEffect, useState } from 'react';
import clsx from 'clsx';
import { getTenants, Tenant } from '../../services/adminService';

export interface TenantSelectorProps {
  value?: number | null;
  onChange: (tenantId: number | null) => void;
  className?: string;
  showAllOption?: boolean;
  disabled?: boolean;
}

export function TenantSelector({
  value,
  onChange,
  className,
  showAllOption = true,
  disabled = false,
}: TenantSelectorProps) {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getTenants({ page_size: 100 });
      setTenants(response.tenants);
    } catch (err) {
      setError('加载租户失败');
      console.error('Failed to load tenants:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedValue = e.target.value;
    if (selectedValue === '') {
      onChange(null);
    } else {
      onChange(parseInt(selectedValue, 10));
    }
  };

  if (loading) {
    return (
      <div className={clsx('flex items-center gap-2 text-slate-400', className)}>
        <div className="w-4 h-4 border-2 border-cyan-500/30 border-t-cyan-500 rounded-full animate-spin" />
        <span className="text-sm">加载中...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={clsx('text-red-400 text-sm', className)}>
        {error}
        <button
          onClick={loadTenants}
          className="ml-2 text-cyan-400 hover:text-cyan-300 underline"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className={clsx('flex items-center gap-2', className)}>
      <label className="text-sm text-slate-400">
        <svg
          className="w-4 h-4 inline-block mr-1"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
          />
        </svg>
        租户:
      </label>
      <select
        value={value ?? ''}
        onChange={handleChange}
        disabled={disabled}
        className={clsx(
          'px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg',
          'text-sm text-slate-200 outline-none transition-all duration-200',
          'focus:border-cyan-500/50 focus:shadow-[0_0_10px_rgba(6,182,212,0.2)]',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'appearance-none bg-no-repeat cursor-pointer min-w-[150px]'
        )}
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`,
          backgroundPosition: 'right 8px center',
          paddingRight: '32px',
        }}
      >
        {showAllOption && (
          <option value="">全部租户</option>
        )}
        {tenants.map((tenant) => (
          <option key={tenant.id} value={tenant.id}>
            {tenant.display_name || tenant.name}
            {!tenant.is_active && ' (已禁用)'}
          </option>
        ))}
      </select>
      {value && (
        <button
          onClick={() => onChange(null)}
          className="p-1 text-slate-400 hover:text-slate-200 transition-colors"
          title="清除选择"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}

export default TenantSelector;
