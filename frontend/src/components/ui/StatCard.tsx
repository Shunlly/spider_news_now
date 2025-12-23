/**
 * HUD 风格 StatCard 组件
 * HUD-style Statistics Card Component
 *
 * 深色主题 + 发光效果
 */

import { ReactNode } from 'react'
import clsx from 'clsx'
import { StoneCard } from './StoneCard'

export interface StatCardProps {
  title: string
  value: number | string
  suffix?: string
  icon?: ReactNode
  iconBg?: string
  loading?: boolean
  trend?: {
    value: number
    isUp: boolean
  }
  className?: string
}

export function StatCard({
  title,
  value,
  suffix,
  icon,
  iconBg = 'bg-cyan-500/20',
  loading = false,
  trend,
  className,
}: StatCardProps) {
  return (
    <StoneCard className={clsx('p-4 h-full', className)} hover={false}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 font-medium">{title}</p>
          {loading ? (
            <div className="h-9 w-24 bg-slate-700/50 rounded animate-pulse mt-2" />
          ) : (
            <p className="text-3xl font-bold text-slate-100 mt-2 tabular-nums font-mono">
              {typeof value === 'number' ? value.toLocaleString() : value}
              {suffix && (
                <span className="text-lg font-normal text-slate-500 ml-1">
                  {suffix}
                </span>
              )}
            </p>
          )}
          {trend && (
            <p
              className={clsx(
                'text-sm mt-2 flex items-center gap-1 font-mono',
                trend.isUp ? 'text-emerald-400' : 'text-red-400'
              )}
            >
              {trend.isUp ? '↑' : '↓'} {Math.abs(trend.value)}%
            </p>
          )}
        </div>
        {icon && (
          <div
            className={clsx(
              'w-10 h-10 rounded-lg flex items-center justify-center border border-cyan-500/30',
              iconBg
            )}
          >
            <span className="text-cyan-400">{icon}</span>
          </div>
        )}
      </div>
    </StoneCard>
  )
}
