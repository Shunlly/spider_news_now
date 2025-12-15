/**
 * GlassCard 组件
 * 毛玻璃卡片组件
 *
 * 遵循宪法 III.A Glassmorphism 设计规范：
 * - backdrop-blur-xl
 * - bg-white/40
 * - border-white/20
 * - rounded-2xl
 */

import { ReactNode } from 'react'
import clsx from 'clsx'

export interface GlassCardProps {
  children: ReactNode
  className?: string
  // 卡片变体
  variant?: 'default' | 'solid' | 'outline'
  // 是否显示悬停效果
  hoverable?: boolean
  // 点击事件
  onClick?: () => void
  // 内边距大小
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
}

const variantStyles = {
  default: 'bg-white/10 backdrop-blur-xl border-white/20',
  solid: 'bg-white/20 backdrop-blur-2xl border-white/30',
  outline: 'bg-transparent backdrop-blur-md border-white/30',
}

export function GlassCard({
  children,
  className,
  variant = 'default',
  hoverable = false,
  onClick,
  padding = 'md',
}: GlassCardProps) {
  return (
    <div
      className={clsx(
        'relative overflow-hidden rounded-2xl border shadow-glass transition-all duration-300',
        variantStyles[variant],
        paddingStyles[padding],
        hoverable && 'cursor-pointer hover:bg-white/15 hover:shadow-glass-lg hover:border-white/30',
        className
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}

export default GlassCard
