/**
 * StatCard 组件
 * 统计数据卡片组件
 *
 * 用于 Bento Grid 布局中展示关键指标
 */

import { ReactNode } from 'react'
import clsx from 'clsx'
import { GlassCard } from './GlassCard'

export interface StatCardProps {
  // 标题
  title: string
  // 数值
  value: number | string
  // 数值后缀（如单位）
  suffix?: string
  // 变化趋势
  trend?: {
    value: number
    isPositive: boolean
  }
  // 图标
  icon?: ReactNode
  // 图标背景色
  iconBg?: string
  // 卡片大小
  size?: 'sm' | 'md' | 'lg'
  // 加载状态
  loading?: boolean
  className?: string
}

const sizeStyles = {
  sm: {
    card: 'p-4',
    value: 'text-2xl',
    title: 'text-xs',
    icon: 'w-10 h-10 text-lg',
  },
  md: {
    card: 'p-5',
    value: 'text-3xl',
    title: 'text-sm',
    icon: 'w-12 h-12 text-xl',
  },
  lg: {
    card: 'p-6',
    value: 'text-4xl',
    title: 'text-base',
    icon: 'w-14 h-14 text-2xl',
  },
}

export function StatCard({
  title,
  value,
  suffix,
  trend,
  icon,
  iconBg = 'bg-indigo-500/30',
  size = 'md',
  loading = false,
  className,
}: StatCardProps) {
  const styles = sizeStyles[size]

  return (
    <GlassCard className={clsx(styles.card, className)} padding="none">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          {/* 标题 */}
          <p className={clsx('text-white/60 mb-2', styles.title)}>{title}</p>

          {/* 数值 */}
          <div className="flex items-baseline gap-1">
            {loading ? (
              <div className={clsx('h-8 w-24 rounded bg-white/10 animate-pulse', styles.value)} />
            ) : (
              <>
                <span className={clsx('font-bold text-white tabular-nums', styles.value)}>
                  {typeof value === 'number' ? value.toLocaleString() : value}
                </span>
                {suffix && (
                  <span className="text-white/50 text-sm">{suffix}</span>
                )}
              </>
            )}
          </div>

          {/* 趋势 */}
          {trend && (
            <div
              className={clsx(
                'flex items-center gap-1 mt-2 text-sm',
                trend.isPositive ? 'text-green-400' : 'text-red-400'
              )}
            >
              <span>{trend.isPositive ? '↑' : '↓'}</span>
              <span>{Math.abs(trend.value)}%</span>
              <span className="text-white/40">较昨日</span>
            </div>
          )}
        </div>

        {/* 图标 */}
        {icon && (
          <div
            className={clsx(
              'rounded-xl flex items-center justify-center text-white',
              iconBg,
              styles.icon
            )}
          >
            {icon}
          </div>
        )}
      </div>
    </GlassCard>
  )
}

export default StatCard
