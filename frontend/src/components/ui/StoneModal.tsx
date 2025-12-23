/**
 * HUD 风格 Modal 组件
 * HUD-style Modal Component
 *
 * 深色主题 + 发光效果
 */

import { ReactNode, useEffect } from 'react'
import { createPortal } from 'react-dom'
import clsx from 'clsx'
import { X } from 'lucide-react'

export interface StoneModalProps {
  open: boolean
  onClose: () => void
  title?: string
  children: ReactNode
  className?: string
  footer?: ReactNode
  width?: 'sm' | 'md' | 'lg' | 'xl'
}

export function StoneModal({
  open,
  onClose,
  title,
  children,
  className,
  footer,
  width = 'md',
}: StoneModalProps) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [open])

  if (!open) return null

  const widths = {
    sm: 'max-w-sm',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  }

  return createPortal(
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
        onClick={onClose}
      />
      {/* Modal */}
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <div
          className={clsx(
            'relative w-full bg-slate-900/95 backdrop-blur-xl rounded-lg border border-slate-700/50 overflow-hidden',
            'shadow-[0_0_30px_rgba(0,0,0,0.5),0_0_60px_rgba(6,182,212,0.1)]',
            'animate-fade-in-up',
            widths[width],
            className
          )}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          {title && (
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50">
              <h3 className="text-lg font-semibold text-cyan-400">{title}</h3>
              <button
                onClick={onClose}
                className="p-2 hover:bg-slate-800/50 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-slate-500 hover:text-slate-300" />
              </button>
            </div>
          )}
          {/* Body */}
          <div className="px-6 py-4 max-h-[70vh] overflow-y-auto text-slate-300">{children}</div>
          {/* Footer */}
          {footer && (
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-700/50 bg-slate-800/30">
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  )
}
