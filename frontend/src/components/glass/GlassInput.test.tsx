import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@/test/utils'
import { GlassInput } from './GlassInput'

describe('GlassInput', () => {
  it('renders input element', () => {
    render(<GlassInput placeholder="Enter text" />)
    expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument()
  })

  it('applies default styles', () => {
    render(<GlassInput data-testid="input" />)
    const input = screen.getByTestId('input')
    expect(input).toHaveClass('bg-transparent')
    expect(input).toHaveClass('text-white')
  })

  it('renders prefix when provided', () => {
    render(<GlassInput prefix={<span data-testid="prefix">@</span>} />)
    expect(screen.getByTestId('prefix')).toBeInTheDocument()
  })

  it('renders suffix when provided', () => {
    render(<GlassInput suffix={<span data-testid="suffix">.com</span>} />)
    expect(screen.getByTestId('suffix')).toBeInTheDocument()
  })

  it('shows error state when error is true', () => {
    render(<GlassInput error data-testid="input" />)
    const wrapper = screen.getByTestId('input').parentElement?.parentElement
    expect(wrapper?.querySelector('.border-red-400\\/50')).toBeTruthy()
  })

  it('displays error message when error and errorMessage are provided', () => {
    render(<GlassInput error errorMessage="This field is required" />)
    expect(screen.getByText('This field is required')).toBeInTheDocument()
    expect(screen.getByText('This field is required')).toHaveClass('text-red-400')
  })

  it('does not display error message when error is false', () => {
    render(<GlassInput errorMessage="This field is required" />)
    expect(screen.queryByText('This field is required')).not.toBeInTheDocument()
  })

  it('handles value changes', () => {
    const handleChange = vi.fn()
    render(<GlassInput onChange={handleChange} data-testid="input" />)

    fireEvent.change(screen.getByTestId('input'), { target: { value: 'test' } })
    expect(handleChange).toHaveBeenCalled()
  })

  it('applies custom className to input', () => {
    render(<GlassInput className="custom-input" data-testid="input" />)
    expect(screen.getByTestId('input')).toHaveClass('custom-input')
  })

  it('forwards ref to input element', () => {
    const ref = vi.fn()
    render(<GlassInput ref={ref} />)
    expect(ref).toHaveBeenCalled()
  })

  it('passes through HTML input attributes', () => {
    render(
      <GlassInput
        type="email"
        name="email"
        required
        maxLength={100}
        data-testid="input"
      />
    )
    const input = screen.getByTestId('input')
    expect(input).toHaveAttribute('type', 'email')
    expect(input).toHaveAttribute('name', 'email')
    expect(input).toHaveAttribute('required')
    expect(input).toHaveAttribute('maxLength', '100')
  })

  it('can be disabled', () => {
    render(<GlassInput disabled data-testid="input" />)
    expect(screen.getByTestId('input')).toBeDisabled()
  })

  it('handles focus and blur events', () => {
    const handleFocus = vi.fn()
    const handleBlur = vi.fn()
    render(
      <GlassInput onFocus={handleFocus} onBlur={handleBlur} data-testid="input" />
    )

    const input = screen.getByTestId('input')
    fireEvent.focus(input)
    expect(handleFocus).toHaveBeenCalled()

    fireEvent.blur(input)
    expect(handleBlur).toHaveBeenCalled()
  })
})
