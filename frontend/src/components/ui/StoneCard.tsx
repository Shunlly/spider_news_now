/**
 * Stone Card 组件
 * Stone-themed Card Component
 */

import { forwardRef, HTMLAttributes } from 'react'
import clsx from 'clsx'

export interface StoneCardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'solid' | 'outline'
  hover?: boolean
}

export const StoneCard = forwardRef<HTMLDivElement, StoneCardProps>(
  ({ className, variant = 'default', hover = true, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'relative overflow-hidden bg-white rounded-xl transition-all duration-300',
          {
            'border border-stone-200 shadow-stone-sm': variant === 'default',
            'shadow-stone': variant === 'solid',
            'border border-stone-200': variant === 'outline',
          },
          hover && 'hover:border-stone-300 hover:shadow-stone-md',
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)

StoneCard.displayName = 'StoneCard'
