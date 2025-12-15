import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/utils'
import { BentoGrid, BentoItem } from './BentoGrid'

describe('BentoGrid', () => {
  it('renders children correctly', () => {
    render(
      <BentoGrid>
        <div>Item 1</div>
        <div>Item 2</div>
      </BentoGrid>
    )
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Item 2')).toBeInTheDocument()
  })

  it('applies default grid styles', () => {
    render(
      <BentoGrid data-testid="grid">
        <div>Content</div>
      </BentoGrid>
    )
    const grid = screen.getByText('Content').parentElement
    expect(grid).toHaveClass('grid')
    expect(grid).toHaveClass('grid-cols-1')
    expect(grid).toHaveClass('md:grid-cols-2')
    expect(grid).toHaveClass('lg:grid-cols-3')
    expect(grid).toHaveClass('xl:grid-cols-4')
  })

  it('applies different gap sizes', () => {
    const { rerender } = render(
      <BentoGrid gap="sm">
        <div>Small Gap</div>
      </BentoGrid>
    )
    expect(screen.getByText('Small Gap').parentElement).toHaveClass('gap-2')

    rerender(
      <BentoGrid gap="md">
        <div>Medium Gap</div>
      </BentoGrid>
    )
    expect(screen.getByText('Medium Gap').parentElement).toHaveClass('gap-4')

    rerender(
      <BentoGrid gap="lg">
        <div>Large Gap</div>
      </BentoGrid>
    )
    expect(screen.getByText('Large Gap').parentElement).toHaveClass('gap-6')
  })

  it('applies custom className', () => {
    render(
      <BentoGrid className="custom-grid">
        <div>Content</div>
      </BentoGrid>
    )
    expect(screen.getByText('Content').parentElement).toHaveClass('custom-grid')
  })

  it('has auto-rows configuration', () => {
    render(
      <BentoGrid>
        <div>Content</div>
      </BentoGrid>
    )
    expect(screen.getByText('Content').parentElement).toHaveClass(
      'auto-rows-[minmax(120px,auto)]'
    )
  })
})

describe('BentoItem', () => {
  it('renders children correctly', () => {
    render(
      <BentoItem>
        <div>Item Content</div>
      </BentoItem>
    )
    expect(screen.getByText('Item Content')).toBeInTheDocument()
  })

  it('applies default col and row span', () => {
    render(
      <BentoItem>
        <div>Default Span</div>
      </BentoItem>
    )
    const item = screen.getByText('Default Span').parentElement
    expect(item).toHaveClass('col-span-1')
    expect(item).toHaveClass('row-span-1')
  })

  it('applies different col spans', () => {
    const { rerender } = render(
      <BentoItem colSpan={1}>
        <div>Span 1</div>
      </BentoItem>
    )
    expect(screen.getByText('Span 1').parentElement).toHaveClass('col-span-1')

    rerender(
      <BentoItem colSpan={2}>
        <div>Span 2</div>
      </BentoItem>
    )
    const span2Item = screen.getByText('Span 2').parentElement
    expect(span2Item).toHaveClass('col-span-1')
    expect(span2Item).toHaveClass('md:col-span-2')

    rerender(
      <BentoItem colSpan={3}>
        <div>Span 3</div>
      </BentoItem>
    )
    const span3Item = screen.getByText('Span 3').parentElement
    expect(span3Item).toHaveClass('col-span-1')
    expect(span3Item).toHaveClass('md:col-span-2')
    expect(span3Item).toHaveClass('lg:col-span-3')

    rerender(
      <BentoItem colSpan={4}>
        <div>Span 4</div>
      </BentoItem>
    )
    const span4Item = screen.getByText('Span 4').parentElement
    expect(span4Item).toHaveClass('xl:col-span-4')
  })

  it('applies different row spans', () => {
    const { rerender } = render(
      <BentoItem rowSpan={1}>
        <div>Row 1</div>
      </BentoItem>
    )
    expect(screen.getByText('Row 1').parentElement).toHaveClass('row-span-1')

    rerender(
      <BentoItem rowSpan={2}>
        <div>Row 2</div>
      </BentoItem>
    )
    expect(screen.getByText('Row 2').parentElement).toHaveClass('row-span-2')

    rerender(
      <BentoItem rowSpan={3}>
        <div>Row 3</div>
      </BentoItem>
    )
    expect(screen.getByText('Row 3').parentElement).toHaveClass('row-span-3')
  })

  it('applies custom className', () => {
    render(
      <BentoItem className="custom-item">
        <div>Content</div>
      </BentoItem>
    )
    expect(screen.getByText('Content').parentElement).toHaveClass('custom-item')
  })

  it('combines col and row spans correctly', () => {
    render(
      <BentoItem colSpan={2} rowSpan={2}>
        <div>Combined</div>
      </BentoItem>
    )
    const item = screen.getByText('Combined').parentElement
    expect(item).toHaveClass('col-span-1')
    expect(item).toHaveClass('md:col-span-2')
    expect(item).toHaveClass('row-span-2')
  })
})
