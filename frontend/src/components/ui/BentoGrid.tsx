/**
 * BentoGrid 组件
 * Bento Grid Layout Component with Stone theme
 */

import { ReactNode } from 'react'
import clsx from 'clsx'
import { StoneCard } from './StoneCard'

export interface BentoGridProps {
  children: ReactNode
  className?: string
  cols?: 1 | 2 | 3 | 4
}

export function BentoGrid({ children, className, cols = 4 }: BentoGridProps) {
  const colsClass = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
  }

  return (
    <div
      className={clsx(
        'grid gap-4 auto-rows-[minmax(120px,auto)]',
        colsClass[cols],
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
  colSpan?: 1 | 2 | 3 | 4
  rowSpan?: 1 | 2 | 3
}

export function BentoItem({
  children,
  className,
  colSpan = 1,
  rowSpan = 1,
}: BentoItemProps) {
  const colSpanClass = {
    1: '',
    2: 'md:col-span-2',
    3: 'md:col-span-2 lg:col-span-3',
    4: 'md:col-span-2 lg:col-span-3 xl:col-span-4',
  }

  const rowSpanClass = {
    1: '',
    2: 'row-span-2',
    3: 'row-span-3',
  }

  return (
    <StoneCard
      className={clsx(
        'p-4',
        colSpanClass[colSpan],
        rowSpanClass[rowSpan],
        className
      )}
      hover={false}
    >
      {children}
    </StoneCard>
  )
}
