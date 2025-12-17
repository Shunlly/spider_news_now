/**
 * Stone Select 组件
 * Stone-themed Select Component
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
          'px-4 py-2 bg-white border rounded-xl text-stone-900',
          'outline-none transition-all duration-200 cursor-pointer',
          'focus:border-stone-400 focus:ring-2 focus:ring-stone-200',
          'appearance-none bg-no-repeat bg-right',
          error ? 'border-red-300' : 'border-stone-200',
          className
        )}
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2378716c' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")`,
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
