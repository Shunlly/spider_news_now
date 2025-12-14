import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/utils'
import { StatCard } from './StatCard'

describe('StatCard', () => {
  it('renders title and value correctly', () => {
    render(<StatCard title="Total Users" value={1234} />)
    expect(screen.getByText('Total Users')).toBeInTheDocument()
    expect(screen.getByText('1,234')).toBeInTheDocument() // Formatted with toLocaleString
  })

  it('renders string value without formatting', () => {
    render(<StatCard title="Status" value="Active" />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders suffix when provided', () => {
    render(<StatCard title="Growth" value={42} suffix="%" />)
    expect(screen.getByText('%')).toBeInTheDocument()
  })

  it('renders positive trend correctly', () => {
    render(
      <StatCard
        title="Revenue"
        value={10000}
        trend={{ value: 15, isPositive: true }}
      />
    )
    expect(screen.getByText('↑')).toBeInTheDocument()
    expect(screen.getByText('15%')).toBeInTheDocument()
    expect(screen.getByText('较昨日')).toBeInTheDocument()
  })

  it('renders negative trend correctly', () => {
    render(
      <StatCard
        title="Errors"
        value={50}
        trend={{ value: 10, isPositive: false }}
      />
    )
    expect(screen.getByText('↓')).toBeInTheDocument()
    expect(screen.getByText('10%')).toBeInTheDocument()
  })

  it('applies positive trend color', () => {
    render(
      <StatCard
        title="Growth"
        value={100}
        trend={{ value: 5, isPositive: true }}
      />
    )
    const trendElement = screen.getByText('↑').parentElement
    expect(trendElement).toHaveClass('text-green-400')
  })

  it('applies negative trend color', () => {
    render(
      <StatCard
        title="Decline"
        value={100}
        trend={{ value: 5, isPositive: false }}
      />
    )
    const trendElement = screen.getByText('↓').parentElement
    expect(trendElement).toHaveClass('text-red-400')
  })

  it('renders icon when provided', () => {
    render(
      <StatCard
        title="Users"
        value={500}
        icon={<span data-testid="icon">👤</span>}
      />
    )
    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('applies custom icon background', () => {
    render(
      <StatCard
        title="Sales"
        value={1000}
        icon={<span>💰</span>}
        iconBg="bg-green-500/30"
      />
    )
    const iconWrapper = screen.getByText('💰').parentElement
    expect(iconWrapper).toHaveClass('bg-green-500/30')
  })

  it('applies different sizes correctly', () => {
    const { rerender } = render(<StatCard title="Small" value={10} size="sm" />)
    expect(screen.getByText('Small')).toHaveClass('text-xs')

    rerender(<StatCard title="Medium" value={10} size="md" />)
    expect(screen.getByText('Medium')).toHaveClass('text-sm')

    rerender(<StatCard title="Large" value={10} size="lg" />)
    expect(screen.getByText('Large')).toHaveClass('text-base')
  })

  it('shows loading skeleton when loading is true', () => {
    render(<StatCard title="Loading" value={0} loading />)
    const skeleton = document.querySelector('.animate-pulse')
    expect(skeleton).toBeInTheDocument()
  })

  it('does not show loading skeleton when loading is false', () => {
    render(<StatCard title="Loaded" value={100} loading={false} />)
    const skeleton = document.querySelector('.animate-pulse')
    expect(skeleton).not.toBeInTheDocument()
  })

  it('applies custom className', () => {
    render(<StatCard title="Custom" value={50} className="custom-stat" />)
    const card = screen.getByText('Custom').closest('.custom-stat')
    expect(card).toBeInTheDocument()
  })

  it('handles zero value correctly', () => {
    render(<StatCard title="Zero" value={0} />)
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('handles large numbers with formatting', () => {
    render(<StatCard title="Large" value={1000000} />)
    expect(screen.getByText('1,000,000')).toBeInTheDocument()
  })
})
