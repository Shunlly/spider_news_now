/**
 * HUD 风格 Input 组件
 * HUD-style Input Component
 *
 * 深色主题 + 发光效果
 */

import { forwardRef, InputHTMLAttributes, ReactNode } from 'react'
import clsx from 'clsx'

export interface StoneInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'prefix'> {
  prefix?: ReactNode
  suffix?: ReactNode
  error?: boolean
}

export const StoneInput = forwardRef<HTMLInputElement, StoneInputProps>(
  ({ className, prefix, suffix, error, ...props }, ref) => {
    return (
      <div className={clsx('relative flex items-center', className)}>
        {prefix && (
          <span className="absolute left-3 text-slate-500">{prefix}</span>
        )}
        <input
          ref={ref}
          className={clsx(
            'w-full px-4 py-2 bg-slate-800/50 border rounded-lg text-slate-200 placeholder-slate-500',
            'outline-none transition-all duration-200',
            'focus:border-cyan-500/50 focus:shadow-[0_0_10px_rgba(6,182,212,0.2)]',
            prefix && 'pl-10',
            suffix && 'pr-10',
            error
              ? 'border-red-500/50 focus:border-red-500/70 focus:shadow-[0_0_10px_rgba(239,68,68,0.2)]'
              : 'border-slate-700/50'
          )}
          {...props}
        />
        {suffix && (
          <span className="absolute right-3 text-slate-500">{suffix}</span>
        )}
      </div>
    )
  }
)

StoneInput.displayName = 'StoneInput'
