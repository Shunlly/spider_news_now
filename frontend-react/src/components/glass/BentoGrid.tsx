/**
 * BentoGrid 组件
 * Bento Grid 布局组件
 *
 * 遵循宪法 III.B Bento Grid 布局规范
 */

import { ReactNode } from 'react'
import clsx from 'clsx'

export interface BentoGridProps {
  children: ReactNode
  className?: string
  // 列数配置
  cols?: {
    default?: number
    sm?: number
    md?: number
    lg?: number
    xl?: number
  }
  // 间距
  gap?: 'sm' | 'md' | 'lg'
}

const gapStyles = {
  sm: 'gap-2',
  md: 'gap-4',
  lg: 'gap-6',
}

export function BentoGrid({
  children,
  className,
  cols: _cols = { default: 1, md: 2, lg: 3, xl: 4 },
  gap = 'md',
}: BentoGridProps) {
  // Note: cols prop is reserved for future dynamic grid configuration
  void _cols

  return (
    <div
      className={clsx(
        'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
        'auto-rows-[minmax(120px,auto)]',
        gapStyles[gap],
        className
      )}
    >
      {children}
    </div>
  )
}

export interface BentoItemProps {
  children: ReactNode
  className?: string
  // 跨列数
  colSpan?: 1 | 2 | 3 | 4
  // 跨行数
  rowSpan?: 1 | 2 | 3
}

const colSpanStyles = {
  1: 'col-span-1',
  2: 'col-span-1 md:col-span-2',
  3: 'col-span-1 md:col-span-2 lg:col-span-3',
  4: 'col-span-1 md:col-span-2 lg:col-span-3 xl:col-span-4',
}

const rowSpanStyles = {
  1: 'row-span-1',
  2: 'row-span-2',
  3: 'row-span-3',
}

export function BentoItem({
  children,
  className,
  colSpan = 1,
  rowSpan = 1,
}: BentoItemProps) {
  return (
    <div
      className={clsx(
        colSpanStyles[colSpan],
        rowSpanStyles[rowSpan],
        className
      )}
    >
      {children}
    </div>
  )
}

export default BentoGrid
