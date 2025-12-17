/**
 * Stone Dropdown 组件
 * Stone-themed Dropdown Component
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
            'bg-white border border-stone-200 rounded-xl shadow-stone-md',
            'animate-fade-in-up',
            position === 'bottom-left' && 'left-0',
            position === 'bottom-right' && 'right-0'
          )}
        >
          {items.map((item) =>
            item.divider ? (
              <div key={item.key} className="my-1 border-t border-stone-100" />
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
                    ? 'text-red-600 hover:bg-red-50'
                    : 'text-stone-700 hover:bg-stone-50'
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
