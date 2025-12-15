/**
 * GlassButton 组件
 * 毛玻璃按钮组件
 *
 * 遵循宪法 III.A Glassmorphism 设计规范
 */

import { ReactNode, ButtonHTMLAttributes } from 'react'
import clsx from 'clsx'
import { Spin } from '@arco-design/web-react'

export interface GlassButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children?: ReactNode
  // 按钮变体
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger'
  // 按钮大小
  size?: 'sm' | 'md' | 'lg'
  // 是否加载中
  loading?: boolean
  // 图标
  icon?: ReactNode
  // 是否块级按钮
  block?: boolean
}

const sizeStyles = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
}

const variantStyles = {
  default: 'bg-white/10 border-white/20 hover:bg-white/20 hover:border-white/30',
  primary: 'bg-indigo-500/50 border-indigo-400/30 hover:bg-indigo-500/70 hover:border-indigo-400/50',
  success: 'bg-green-500/50 border-green-400/30 hover:bg-green-500/70 hover:border-green-400/50',
  warning: 'bg-yellow-500/50 border-yellow-400/30 hover:bg-yellow-500/70 hover:border-yellow-400/50',
  danger: 'bg-red-500/50 border-red-400/30 hover:bg-red-500/70 hover:border-red-400/50',
}

export function GlassButton({
  children,
  className,
  variant = 'default',
  size = 'md',
  loading = false,
  icon,
  block = false,
  disabled,
  ...props
}: GlassButtonProps) {
  return (
    <button
      className={clsx(
        'relative inline-flex items-center justify-center gap-2',
        'backdrop-blur-md border rounded-xl',
        'text-white font-medium',
        'transition-all duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        'active:scale-95',
        sizeStyles[size],
        variantStyles[variant],
        block && 'w-full',
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <Spin size={size === 'sm' ? 12 : size === 'lg' ? 20 : 16} />
      ) : icon ? (
        <span className="text-lg">{icon}</span>
      ) : null}
      {children && <span>{children}</span>}
    </button>
  )
}

export default GlassButton
