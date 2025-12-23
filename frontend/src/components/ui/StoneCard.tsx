/**
 * HUD 风格 Card 组件
 * HUD-style Card Component
 *
 * 深色主题 + 发光效果
 */

import { forwardRef, HTMLAttributes } from 'react'
import clsx from 'clsx'

export interface StoneCardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'solid' | 'outline' | 'glass'
  hover?: boolean
  glow?: boolean
}

export const StoneCard = forwardRef<HTMLDivElement, StoneCardProps>(
  ({ className, variant = 'default', hover = true, glow = false, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'relative overflow-hidden rounded-xl transition-all duration-300',
          {
            // Default: 深色半透明背景 + 边框
            'bg-slate-900/50 border border-slate-700/50 backdrop-blur-sm': variant === 'default',
            // Solid: 实心深色背景
            'bg-slate-900 border border-slate-700/50': variant === 'solid',
            // Outline: 仅边框
            'bg-transparent border border-slate-700/50': variant === 'outline',
            // Glass: 玻璃态
            'bg-slate-800/30 border border-slate-600/30 backdrop-blur-xl': variant === 'glass',
          },
          hover && 'hover:border-cyan-500/30 hover:shadow-[0_0_15px_rgba(6,182,212,0.1)]',
          glow && 'shadow-[0_0_20px_rgba(6,182,212,0.15)]',
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
