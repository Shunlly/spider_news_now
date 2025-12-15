import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@/test/utils'
import { GlassButton } from './GlassButton'

// Mock Arco Design Spin component
vi.mock('@arco-design/web-react', () => ({
  Spin: ({ size }: { size: number }) => <span data-testid="spin" data-size={size}>Loading...</span>,
}))

describe('GlassButton', () => {
  it('renders children correctly', () => {
    render(<GlassButton>Click me</GlassButton>)
    expect(screen.getByRole('button')).toHaveTextContent('Click me')
  })

  it('applies default styles', () => {
    render(<GlassButton>Button</GlassButton>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('backdrop-blur-md')
    expect(button).toHaveClass('rounded-xl')
    expect(button).toHaveClass('px-4') // default md size
    expect(button).toHaveClass('py-2')
  })

  it('applies different variants correctly', () => {
    const { rerender } = render(<GlassButton variant="default">Default</GlassButton>)
    expect(screen.getByRole('button')).toHaveClass('bg-white/10')

    rerender(<GlassButton variant="primary">Primary</GlassButton>)
    expect(screen.getByRole('button')).toHaveClass('bg-indigo-500/50')

    rerender(<GlassButton variant="success">Success</GlassButton>)
    expect(screen.getByRole('button')).toHaveClass('bg-green-500/50')

    rerender(<GlassButton variant="warning">Warning</GlassButton>)
    expect(screen.getByRole('button')).toHaveClass('bg-yellow-500/50')

    rerender(<GlassButton variant="danger">Danger</GlassButton>)
    expect(screen.getByRole('button')).toHaveClass('bg-red-500/50')
  })

  it('applies different sizes correctly', () => {
    const { rerender } = render(<GlassButton size="sm">Small</GlassButton>)
    expect(screen.getByRole('button')).toHaveClass('px-3')
    expect(screen.getByRole('button')).toHaveClass('py-1.5')

    rerender(<GlassButton size="md">Medium</GlassButton>)
    expect(screen.getByRole('button')).toHaveClass('px-4')
    expect(screen.getByRole('button')).toHaveClass('py-2')

    rerender(<GlassButton size="lg">Large</GlassButton>)
    expect(screen.getByRole('button')).toHaveClass('px-6')
    expect(screen.getByRole('button')).toHaveClass('py-3')
  })

  it('shows loading spinner when loading is true', () => {
    render(<GlassButton loading>Loading</GlassButton>)
    expect(screen.getByTestId('spin')).toBeInTheDocument()
  })

  it('disables button when loading', () => {
    render(<GlassButton loading>Loading</GlassButton>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('disables button when disabled prop is true', () => {
    render(<GlassButton disabled>Disabled</GlassButton>)
    expect(screen.getByRole('button')).toBeDisabled()
    expect(screen.getByRole('button')).toHaveClass('disabled:opacity-50')
  })

  it('renders icon when provided', () => {
    render(<GlassButton icon={<span data-testid="icon">+</span>}>With Icon</GlassButton>)
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('applies block style when block is true', () => {
    render(<GlassButton block>Block</GlassButton>)
    expect(screen.getByRole('button')).toHaveClass('w-full')
  })

  it('calls onClick handler when clicked', () => {
    const handleClick = vi.fn()
    render(<GlassButton onClick={handleClick}>Click</GlassButton>)

    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not call onClick when disabled', () => {
    const handleClick = vi.fn()
    render(<GlassButton disabled onClick={handleClick}>Disabled</GlassButton>)

    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('applies custom className', () => {
    render(<GlassButton className="custom-class">Custom</GlassButton>)
    expect(screen.getByRole('button')).toHaveClass('custom-class')
  })

  it('passes through HTML button attributes', () => {
    render(<GlassButton type="submit" name="test-button">Submit</GlassButton>)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('type', 'submit')
    expect(button).toHaveAttribute('name', 'test-button')
  })
})
