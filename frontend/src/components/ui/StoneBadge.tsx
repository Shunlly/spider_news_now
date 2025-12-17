/**
 * Stone Badge 组件
 * Stone-themed Badge Component
 */

import { ReactNode } from 'react'
import clsx from 'clsx'

export interface StoneBadgeProps {
  children: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info'
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
    default: 'bg-stone-100 text-stone-700',
    success: 'bg-green-100 text-green-700',
    warning: 'bg-yellow-100 text-yellow-700',
    danger: 'bg-red-100 text-red-700',
    info: 'bg-blue-100 text-blue-700',
  }

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  }

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-md font-medium',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  )
}
