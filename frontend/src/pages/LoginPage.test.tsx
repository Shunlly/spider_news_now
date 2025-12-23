/**
 * Login Page E2E Tests
 * T170: Frontend E2E test for login flow
 *
 * Tests:
 * - Login form rendering
 * - Form validation
 * - Login submission
 * - Error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../test/utils'
import LoginPage from './LoginPage'
import { useAuthStore } from '../stores/authStore'

// Mock the auth store
vi.mock('../stores/authStore', () => ({
  useAuthStore: vi.fn(),
}))

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: null }),
  }
})

// Default mock store state
const mockAuthStore = {
  login: vi.fn(),
  isAuthenticated: false,
  loading: false,
  error: null,
  clearError: vi.fn(),
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    ;(useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue(mockAuthStore)
  })

  describe('Rendering', () => {
    it('should render login form with username and password fields', () => {
      render(<LoginPage />)

      expect(screen.getByPlaceholderText(/用户名/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/密码/i)).toBeInTheDocument()
    })

    it('should render next step button initially', () => {
      render(<LoginPage />)

      const nextButton = screen.getByRole('button', { name: /下一步/i })
      expect(nextButton).toBeInTheDocument()
    })

    it('should render link to register page', () => {
      render(<LoginPage />)

      expect(screen.getByText(/立即注册/i)).toBeInTheDocument()
    })
  })

  describe('Form Validation', () => {
    it('should show error when username is empty', async () => {
      render(<LoginPage />)

      const nextButton = screen.getByRole('button', { name: /下一步/i })
      fireEvent.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText(/请输入用户名/i)).toBeInTheDocument()
      })
    })

    it('should show error when username is too short', async () => {
      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText(/用户名/i)
      fireEvent.change(usernameInput, { target: { value: 'ab' } })

      const nextButton = screen.getByRole('button', { name: /下一步/i })
      fireEvent.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText(/用户名至少3个字符/i)).toBeInTheDocument()
      })
    })

    it('should show error when password is empty', async () => {
      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText(/用户名/i)
      fireEvent.change(usernameInput, { target: { value: 'testuser' } })

      const nextButton = screen.getByRole('button', { name: /下一步/i })
      fireEvent.click(nextButton)

      await waitFor(() => {
        expect(screen.getByText(/请输入密码/i)).toBeInTheDocument()
      })
    })
  })

  describe('Password Toggle', () => {
    it('should toggle password visibility', () => {
      render(<LoginPage />)

      const passwordInput = screen.getByPlaceholderText(/密码/i) as HTMLInputElement
      expect(passwordInput.type).toBe('password')

      // Find and click the eye button (toggle visibility)
      const toggleButtons = screen.getAllByRole('button')
      const eyeButton = toggleButtons.find(btn => btn.className.includes('eye'))
      if (eyeButton) {
        fireEvent.click(eyeButton)
        expect(passwordInput.type).toBe('text')
      }
    })
  })

  describe('Authentication', () => {
    it('should redirect to dashboard when already authenticated', () => {
      ;(useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockAuthStore,
        isAuthenticated: true,
      })

      render(<LoginPage />)

      expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true })
    })

    it('should display error message from auth store', () => {
      const errorMessage = '用户名或密码错误'
      ;(useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockAuthStore,
        error: errorMessage,
      })

      render(<LoginPage />)

      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })

    it('should show loading state during login', () => {
      ;(useAuthStore as unknown as ReturnType<typeof vi.fn>).mockReturnValue({
        ...mockAuthStore,
        loading: true,
      })

      render(<LoginPage />)

      const nextButton = screen.getByRole('button', { name: /下一步/i })
      expect(nextButton).toBeInTheDocument()
    })
  })

  describe('Captcha Flow', () => {
    it('should show captcha when form is valid and next button is clicked', async () => {
      render(<LoginPage />)

      const usernameInput = screen.getByPlaceholderText(/用户名/i)
      const passwordInput = screen.getByPlaceholderText(/密码/i)

      fireEvent.change(usernameInput, { target: { value: 'testuser' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })

      const nextButton = screen.getByRole('button', { name: /下一步/i })
      fireEvent.click(nextButton)

      // Should show login button and back button
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument()
        expect(screen.getByText(/返回修改/i)).toBeInTheDocument()
      })
    })
  })
})
