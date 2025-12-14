/**
 * GlassInput 组件
 * 毛玻璃输入框组件
 */

import { InputHTMLAttributes, forwardRef, ReactNode } from 'react'
import clsx from 'clsx'

export interface GlassInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'prefix'> {
  // 前缀图标
  prefix?: ReactNode
  // 后缀图标
  suffix?: ReactNode
  // 是否有错误
  error?: boolean
  // 错误信息
  errorMessage?: string
}

export const GlassInput = forwardRef<HTMLInputElement, GlassInputProps>(
  ({ className, prefix, suffix, error, errorMessage, ...props }, ref) => {
    return (
      <div className="relative">
        <div
          className={clsx(
            'flex items-center gap-2',
            'bg-white/5 backdrop-blur-md',
            'border rounded-xl',
            'transition-all duration-200',
            error
              ? 'border-red-400/50 focus-within:ring-2 focus-within:ring-red-500/30'
              : 'border-white/10 focus-within:bg-white/10 focus-within:border-white/30 focus-within:ring-2 focus-within:ring-indigo-500/30'
          )}
        >
          {prefix && (
            <span className="pl-4 text-white/40">{prefix}</span>
          )}
          <input
            ref={ref}
            className={clsx(
              'flex-1 px-4 py-2 bg-transparent',
              'text-white placeholder-white/40',
              'outline-none',
              prefix && 'pl-0',
              suffix && 'pr-0',
              className
            )}
            {...props}
          />
          {suffix && (
            <span className="pr-4 text-white/40">{suffix}</span>
          )}
        </div>
        {error && errorMessage && (
          <p className="mt-1 text-sm text-red-400">{errorMessage}</p>
        )}
      </div>
    )
  }
)

GlassInput.displayName = 'GlassInput'

export default GlassInput
