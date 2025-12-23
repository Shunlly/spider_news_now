/**
 * HUD 风格 Select 组件
 * HUD-style Select Component
 *
 * 深色主题 + 发光效果
 */

import { forwardRef, SelectHTMLAttributes } from 'react'
import clsx from 'clsx'

export interface StoneSelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  error?: boolean
}

export const StoneSelect = forwardRef<HTMLSelectElement, StoneSelectProps>(
  ({ className, error, children, ...props }, ref) => {
    return (
      <select
        ref={ref}
        className={clsx(
          'px-4 py-2 bg-slate-800/50 border rounded-lg text-slate-200',
          'outline-none transition-all duration-200 cursor-pointer',
          'focus:border-cyan-500/50 focus:shadow-[0_0_10px_rgba(6,182,212,0.2)]',
          'appearance-none bg-no-repeat bg-right',
          error ? 'border-red-500/50' : 'border-slate-700/50',
          className
        )}
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`,
          backgroundPosition: 'right 12px center',
          paddingRight: '40px',
        }}
        {...props}
      >
        {children}
      </select>
    )
  }
)

StoneSelect.displayName = 'StoneSelect'
