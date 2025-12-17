/**
 * 全局错误边界组件
 * Global Error Boundary Component
 *
 * 捕获子组件树中的 JavaScript 错误，显示备用 UI
 */

import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import { StoneButton } from './ui'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo })

    // 可以在这里添加错误上报逻辑
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  handleReload = () => {
    window.location.reload()
  }

  handleGoHome = () => {
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      // 如果提供了自定义 fallback，使用它
      if (this.props.fallback) {
        return this.props.fallback
      }

      // 默认错误 UI
      return (
        <div className="min-h-screen bg-stone-200 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>

            <h1 className="text-xl font-semibold text-stone-900 mb-2">
              出错了
            </h1>

            <p className="text-stone-600 mb-6">
              应用程序遇到了意外错误。请尝试刷新页面或返回首页。
            </p>

            {/* 开发环境显示错误详情 */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="mb-6 text-left">
                <summary className="cursor-pointer text-sm text-stone-500 hover:text-stone-700">
                  查看错误详情
                </summary>
                <div className="mt-2 p-3 bg-stone-100 rounded-lg overflow-auto max-h-40">
                  <pre className="text-xs text-red-600 whitespace-pre-wrap">
                    {this.state.error.toString()}
                    {this.state.errorInfo?.componentStack}
                  </pre>
                </div>
              </details>
            )}

            <div className="flex gap-3 justify-center">
              <StoneButton
                variant="secondary"
                onClick={this.handleGoHome}
              >
                <Home className="w-4 h-4 mr-2" />
                返回首页
              </StoneButton>

              <StoneButton
                variant="primary"
                onClick={this.handleReload}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                刷新页面
              </StoneButton>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

/**
 * 页面级别的错误边界
 * 用于包裹单个页面，错误不会影响整个应用
 */
export function PageErrorBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary
      fallback={
        <div className="p-8 text-center">
          <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-6 h-6 text-red-500" />
          </div>
          <h2 className="text-lg font-medium text-stone-900 mb-2">
            页面加载失败
          </h2>
          <p className="text-stone-600 mb-4">
            该页面无法正常加载，请稍后重试。
          </p>
          <StoneButton
            variant="secondary"
            onClick={() => window.location.reload()}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            重新加载
          </StoneButton>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  )
}
