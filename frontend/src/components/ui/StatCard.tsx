/**
 * StatCard 组件
 * Statistics Card Component with Stone theme
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
  iconBg = 'bg-stone-100',
  loading = false,
  trend,
  className,
}: StatCardProps) {
  return (
    <StoneCard className={clsx('p-4 h-full', className)} hover={false}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-stone-500 font-medium">{title}</p>
          {loading ? (
            <div className="h-9 w-24 bg-stone-100 rounded animate-pulse mt-2" />
          ) : (
            <p className="text-3xl font-bold text-stone-900 mt-2 tabular-nums">
              {typeof value === 'number' ? value.toLocaleString() : value}
              {suffix && (
                <span className="text-lg font-normal text-stone-400 ml-1">
                  {suffix}
                </span>
              )}
            </p>
          )}
          {trend && (
            <p
              className={clsx(
                'text-sm mt-2 flex items-center gap-1',
                trend.isUp ? 'text-green-600' : 'text-red-600'
              )}
            >
              {trend.isUp ? '↑' : '↓'} {Math.abs(trend.value)}%
            </p>
          )}
        </div>
        {icon && (
          <div
            className={clsx(
              'w-10 h-10 rounded-lg flex items-center justify-center',
              iconBg
            )}
          >
            <span className="text-stone-600">{icon}</span>
          </div>
        )}
      </div>
    </StoneCard>
  )
}
