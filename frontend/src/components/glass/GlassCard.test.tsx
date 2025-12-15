import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { GlassCard } from './GlassCard'

describe('GlassCard', () => {
  it('renders children correctly', () => {
    render(<GlassCard>Test Content</GlassCard>)
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('applies default styles', () => {
    const { container } = render(<GlassCard>Content</GlassCard>)
    const card = container.firstChild as HTMLElement
    expect(card).toHaveClass('rounded-2xl')
    expect(card).toHaveClass('backdrop-blur-xl')
    expect(card).toHaveClass('p-4') // default md padding
  })

  it('applies different variants correctly', () => {
    const { container, rerender } = render(<GlassCard variant="default">Default</GlassCard>)
    expect(container.firstChild).toHaveClass('bg-white/10')

    rerender(<GlassCard variant="solid">Solid</GlassCard>)
    expect(container.firstChild).toHaveClass('bg-white/20')

    rerender(<GlassCard variant="outline">Outline</GlassCard>)
    expect(container.firstChild).toHaveClass('bg-transparent')
  })

  it('applies different padding sizes', () => {
    const { container, rerender } = render(<GlassCard padding="none">None</GlassCard>)
    const card = container.firstChild as HTMLElement
    expect(card).not.toHaveClass('p-3')
    expect(card).not.toHaveClass('p-4')
    expect(card).not.toHaveClass('p-6')

    rerender(<GlassCard padding="sm">Small</GlassCard>)
    expect(container.firstChild).toHaveClass('p-3')

    rerender(<GlassCard padding="md">Medium</GlassCard>)
    expect(container.firstChild).toHaveClass('p-4')

    rerender(<GlassCard padding="lg">Large</GlassCard>)
    expect(container.firstChild).toHaveClass('p-6')
  })

  it('applies hoverable styles when hoverable is true', () => {
    const { container } = render(<GlassCard hoverable>Hoverable</GlassCard>)
    const card = container.firstChild as HTMLElement
    expect(card).toHaveClass('cursor-pointer')
    expect(card).toHaveClass('hover:bg-white/15')
  })

  it('does not apply hoverable styles when hoverable is false', () => {
    const { container } = render(<GlassCard hoverable={false}>Not Hoverable</GlassCard>)
    const card = container.firstChild as HTMLElement
    expect(card).not.toHaveClass('cursor-pointer')
  })

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn()
    const { container } = render(<GlassCard onClick={handleClick}>Clickable</GlassCard>)

    fireEvent.click(container.firstChild as HTMLElement)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('applies custom className', () => {
    const { container } = render(<GlassCard className="custom-class">Custom</GlassCard>)
    expect(container.firstChild).toHaveClass('custom-class')
  })
})
