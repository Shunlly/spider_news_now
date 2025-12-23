/**
 * HUD 风格 Button 组件
 * HUD-style Button Component
 *
 * 深色主题 + 发光效果
 */

import { forwardRef, ButtonHTMLAttributes, ReactNode } from 'react'
import clsx from 'clsx'
import { Loader2 } from 'lucide-react'

export interface StoneButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  icon?: ReactNode
}

export const StoneButton = forwardRef<HTMLButtonElement, StoneButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      loading = false,
      icon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 cursor-pointer active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 disabled:hover:shadow-none'

    const variants = {
      primary: 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 hover:bg-cyan-500/30 hover:shadow-[0_0_15px_rgba(6,182,212,0.3)] hover:-translate-y-0.5',
      secondary: 'bg-slate-800/50 text-slate-300 border border-slate-700/50 hover:border-slate-600 hover:bg-slate-800/70 hover:text-slate-200',
      ghost: 'bg-transparent text-slate-400 hover:bg-slate-800/50 hover:text-cyan-400',
      danger: 'bg-red-500/20 text-red-400 border border-red-500/50 hover:bg-red-500/30 hover:shadow-[0_0_15px_rgba(239,68,68,0.3)] hover:-translate-y-0.5',
    }

    const sizes = {
      sm: 'px-3 py-1.5 text-xs gap-1.5',
      md: 'px-4 py-2 text-sm gap-2',
      lg: 'px-6 py-3 text-base gap-2',
    }

    return (
      <button
        ref={ref}
        className={clsx(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : icon ? (
          <span className="w-4 h-4">{icon}</span>
        ) : null}
        {children}
      </button>
    )
  }
)

StoneButton.displayName = 'StoneButton'
