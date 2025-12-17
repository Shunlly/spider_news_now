/**
 * Stone Input 组件
 * Stone-themed Input Component
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
          <span className="absolute left-3 text-stone-400">{prefix}</span>
        )}
        <input
          ref={ref}
          className={clsx(
            'w-full px-4 py-2 bg-white border rounded-xl text-stone-900 placeholder-stone-400',
            'outline-none transition-all duration-200',
            'focus:border-stone-400 focus:ring-2 focus:ring-stone-200',
            prefix && 'pl-10',
            suffix && 'pr-10',
            error ? 'border-red-300 focus:border-red-400 focus:ring-red-200' : 'border-stone-200'
          )}
          {...props}
        />
        {suffix && (
          <span className="absolute right-3 text-stone-400">{suffix}</span>
        )}
      </div>
    )
  }
)

StoneInput.displayName = 'StoneInput'
