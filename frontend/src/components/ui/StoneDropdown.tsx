/**
 * HUD 风格 Dropdown 组件
 * HUD-style Dropdown Component
 *
 * 深色主题 + 发光效果
 */

import { useState, useRef, useEffect, ReactNode } from 'react'
import clsx from 'clsx'

export interface DropdownItem {
  key: string
  label: ReactNode
  icon?: ReactNode
  onClick?: () => void
  danger?: boolean
  divider?: boolean
}

export interface StoneDropdownProps {
  trigger: ReactNode
  items: DropdownItem[]
  position?: 'bottom-left' | 'bottom-right'
  className?: string
}

export function StoneDropdown({
  trigger,
  items,
  position = 'bottom-right',
  className,
}: StoneDropdownProps) {
  const [open, setOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div ref={dropdownRef} className={clsx('relative inline-block', className)}>
      <div onClick={() => setOpen(!open)} className="cursor-pointer">
        {trigger}
      </div>
      {open && (
        <div
          className={clsx(
            'absolute z-50 mt-2 min-w-[160px] py-1',
            'bg-slate-900/95 backdrop-blur-xl border border-slate-700/50 rounded-lg',
            'shadow-[0_0_20px_rgba(0,0,0,0.5)]',
            'animate-fade-in-up',
            position === 'bottom-left' && 'left-0',
            position === 'bottom-right' && 'right-0'
          )}
        >
          {items.map((item) =>
            item.divider ? (
              <div key={item.key} className="my-1 border-t border-slate-700/50" />
            ) : (
              <button
                key={item.key}
                onClick={() => {
                  item.onClick?.()
                  setOpen(false)
                }}
                className={clsx(
                  'w-full flex items-center gap-2 px-4 py-2 text-sm text-left',
                  'transition-colors',
                  item.danger
                    ? 'text-red-400 hover:bg-red-500/20'
                    : 'text-slate-300 hover:bg-slate-800/50 hover:text-cyan-400'
                )}
              >
                {item.icon && <span className="w-4 h-4">{item.icon}</span>}
                {item.label}
              </button>
            )
          )}
        </div>
      )}
    </div>
  )
}
