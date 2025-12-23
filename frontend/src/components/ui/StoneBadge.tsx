/**
 * HUD 风格 Badge 组件
 * HUD-style Badge Component
 *
 * 深色主题 + 发光效果
 */

import { ReactNode } from 'react'
import clsx from 'clsx'

export interface StoneBadgeProps {
  children: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'cyan' | 'purple'
  size?: 'sm' | 'md'
  className?: string
}

export function StoneBadge({
  children,
  variant = 'default',
  size = 'sm',
  className,
}: StoneBadgeProps) {
  const variants = {
    default: 'bg-slate-500/20 text-slate-400 border border-slate-500/30',
    success: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30',
    warning: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
    danger: 'bg-red-500/20 text-red-400 border border-red-500/30',
    info: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
    cyan: 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30',
    purple: 'bg-purple-500/20 text-purple-400 border border-purple-500/30',
  }

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded font-medium font-mono',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  )
}
