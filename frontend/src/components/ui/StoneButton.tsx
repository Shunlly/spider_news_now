/**
 * Stone Button 组件
 * Stone-themed Button Component
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
    const baseStyles = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 cursor-pointer active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0'

    const variants = {
      primary: 'bg-stone-900 text-white hover:bg-stone-800 hover:shadow-stone-md hover:-translate-y-0.5',
      secondary: 'bg-white text-stone-700 border border-stone-200 hover:border-stone-300 hover:bg-stone-50',
      ghost: 'bg-transparent text-stone-600 hover:bg-stone-100 hover:text-stone-900',
      danger: 'bg-red-600 text-white hover:bg-red-700 hover:shadow-stone-md hover:-translate-y-0.5',
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
