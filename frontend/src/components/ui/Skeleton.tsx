/**
 * 骨架屏组件
 * Skeleton Loading Components
 *
 * 提供多种骨架屏样式，用于内容加载时的占位
 */

import clsx from 'clsx'

interface SkeletonProps {
  className?: string
  style?: React.CSSProperties
}

/**
 * 基础骨架块
 */
export function Skeleton({ className, style }: SkeletonProps) {
  return (
    <div
      className={clsx(
        'animate-pulse bg-stone-200 rounded',
        className
      )}
      style={style}
    />
  )
}

/**
 * 文本骨架
 */
export function SkeletonText({
  lines = 3,
  className
}: {
  lines?: number
  className?: string
}) {
  return (
    <div className={clsx('space-y-2', className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={clsx(
            'h-4',
            i === lines - 1 ? 'w-4/5' : 'w-full'
          )}
        />
      ))}
    </div>
  )
}

/**
 * 头像骨架
 */
export function SkeletonAvatar({
  size = 'md',
  className
}: {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
  }

  return (
    <Skeleton
      className={clsx(
        'rounded-full',
        sizeClasses[size],
        className
      )}
    />
  )
}

/**
 * 卡片骨架
 */
export function SkeletonCard({ className }: SkeletonProps) {
  return (
    <div className={clsx(
      'bg-white rounded-xl border border-stone-200 p-4',
      className
    )}>
      <div className="flex items-center gap-3 mb-4">
        <SkeletonAvatar size="md" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-3 w-1/4" />
        </div>
      </div>
      <SkeletonText lines={3} />
    </div>
  )
}

/**
 * 新闻列表项骨架
 */
export function SkeletonNewsItem({ className }: SkeletonProps) {
  return (
    <div className={clsx(
      'bg-white rounded-xl border border-stone-200 p-4 flex gap-4',
      className
    )}>
      {/* 缩略图 */}
      <Skeleton className="w-24 h-24 rounded-lg flex-shrink-0" />

      {/* 内容 */}
      <div className="flex-1 min-w-0">
        <Skeleton className="h-5 w-3/4 mb-2" />
        <Skeleton className="h-4 w-full mb-1" />
        <Skeleton className="h-4 w-2/3 mb-3" />
        <div className="flex gap-2">
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="h-5 w-20 rounded-full" />
        </div>
      </div>
    </div>
  )
}

/**
 * 统计卡片骨架
 */
export function SkeletonStatCard({ className }: SkeletonProps) {
  return (
    <div className={clsx(
      'bg-white rounded-xl border border-stone-200 p-5',
      className
    )}>
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-4 w-20" />
        <Skeleton className="w-10 h-10 rounded-lg" />
      </div>
      <Skeleton className="h-8 w-24 mb-2" />
      <Skeleton className="h-3 w-32" />
    </div>
  )
}

/**
 * 表格行骨架
 */
export function SkeletonTableRow({
  columns = 4,
  className
}: {
  columns?: number
  className?: string
}) {
  return (
    <tr className={className}>
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton className="h-4 w-full" />
        </td>
      ))}
    </tr>
  )
}

/**
 * 表格骨架
 */
export function SkeletonTable({
  rows = 5,
  columns = 4,
  className
}: {
  rows?: number
  columns?: number
  className?: string
}) {
  return (
    <div className={clsx(
      'bg-white rounded-xl border border-stone-200 overflow-hidden',
      className
    )}>
      <table className="w-full">
        <thead className="bg-stone-50 border-b border-stone-200">
          <tr>
            {Array.from({ length: columns }).map((_, i) => (
              <th key={i} className="px-4 py-3 text-left">
                <Skeleton className="h-4 w-20" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-stone-100">
          {Array.from({ length: rows }).map((_, i) => (
            <SkeletonTableRow key={i} columns={columns} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

/**
 * 图表骨架
 */
export function SkeletonChart({ className }: SkeletonProps) {
  return (
    <div className={clsx(
      'bg-white rounded-xl border border-stone-200 p-4',
      className
    )}>
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-5 w-32" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20 rounded-lg" />
          <Skeleton className="h-8 w-20 rounded-lg" />
        </div>
      </div>

      {/* 图表区域 */}
      <div className="h-64 flex items-end gap-2 pt-4">
        {Array.from({ length: 12 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1 rounded-t"
            style={{ height: `${Math.random() * 60 + 40}%` }}
          />
        ))}
      </div>

      {/* X轴标签 */}
      <div className="flex justify-between mt-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-3 w-10" />
        ))}
      </div>
    </div>
  )
}

/**
 * 仪表盘页面骨架
 */
export function SkeletonDashboard() {
  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonStatCard key={i} />
        ))}
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SkeletonChart />
        <SkeletonChart />
      </div>

      {/* 列表 */}
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <SkeletonNewsItem key={i} />
        ))}
      </div>
    </div>
  )
}

/**
 * 新闻页面骨架
 */
export function SkeletonNewsList() {
  return (
    <div className="space-y-4">
      {/* 搜索栏 */}
      <div className="flex gap-4">
        <Skeleton className="h-10 flex-1 rounded-xl" />
        <Skeleton className="h-10 w-32 rounded-xl" />
      </div>

      {/* 新闻列表 */}
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <SkeletonNewsItem key={i} />
        ))}
      </div>

      {/* 分页 */}
      <div className="flex justify-center gap-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="w-10 h-10 rounded-lg" />
        ))}
      </div>
    </div>
  )
}
