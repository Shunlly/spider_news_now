/**
 * HUD 风格 Toast 通知组件
 * HUD-style Toast Notification Component
 *
 * 深色主题 + 发光效果
 */

import { useEffect, useState, useCallback, createContext, useContext } from 'react'
import { createPortal } from 'react-dom'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import clsx from 'clsx'

type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  type: ToastType
  message: string
  duration?: number
}

interface ToastContextValue {
  toasts: Toast[]
  addToast: (type: ToastType, message: string, duration?: number) => void
  removeToast: (id: string) => void
  success: (message: string, duration?: number) => void
  error: (message: string, duration?: number) => void
  warning: (message: string, duration?: number) => void
  info: (message: string, duration?: number) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

// HUD Toast 配置
const toastConfig = {
  success: {
    icon: CheckCircle,
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    text: 'text-emerald-400',
    iconColor: 'text-emerald-400',
    glow: 'shadow-[0_0_15px_rgba(16,185,129,0.2)]',
  },
  error: {
    icon: XCircle,
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    text: 'text-red-400',
    iconColor: 'text-red-400',
    glow: 'shadow-[0_0_15px_rgba(239,68,68,0.2)]',
  },
  warning: {
    icon: AlertTriangle,
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
    text: 'text-yellow-400',
    iconColor: 'text-yellow-400',
    glow: 'shadow-[0_0_15px_rgba(234,179,8,0.2)]',
  },
  info: {
    icon: Info,
    bg: 'bg-cyan-500/10',
    border: 'border-cyan-500/30',
    text: 'text-cyan-400',
    iconColor: 'text-cyan-400',
    glow: 'shadow-[0_0_15px_rgba(6,182,212,0.2)]',
  },
}

// 单个 Toast 项
function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const [isExiting, setIsExiting] = useState(false)
  const config = toastConfig[toast.type]
  const Icon = config.icon

  useEffect(() => {
    const duration = toast.duration || 3000
    const timer = setTimeout(() => {
      setIsExiting(true)
      setTimeout(onClose, 300)
    }, duration)

    return () => clearTimeout(timer)
  }, [toast.duration, onClose])

  const handleClose = () => {
    setIsExiting(true)
    setTimeout(onClose, 300)
  }

  return (
    <div
      className={clsx(
        'flex items-center gap-3 px-4 py-3 rounded-lg border backdrop-blur-xl min-w-[300px] max-w-[400px]',
        config.bg,
        config.border,
        config.glow,
        'transition-all duration-300',
        isExiting ? 'opacity-0 translate-x-4' : 'opacity-100 translate-x-0'
      )}
    >
      <Icon className={clsx('w-5 h-5 flex-shrink-0', config.iconColor)} />
      <p className={clsx('flex-1 text-sm', config.text)}>{toast.message}</p>
      <button
        onClick={handleClose}
        className={clsx(
          'p-1 rounded-lg hover:bg-slate-700/50 transition-colors',
          'text-slate-500 hover:text-slate-300'
        )}
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

// Toast 容器
function ToastContainer({ toasts, removeToast }: { toasts: Toast[]; removeToast: (id: string) => void }) {
  if (toasts.length === 0) return null

  return createPortal(
    <div className="fixed top-4 right-4 z-[9999] flex flex-col gap-2">
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>,
    document.body
  )
}

// Toast Provider
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const addToast = useCallback((type: ToastType, message: string, duration?: number) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    setToasts((prev) => [...prev, { id, type, message, duration }])
  }, [])

  const success = useCallback((message: string, duration?: number) => {
    addToast('success', message, duration)
  }, [addToast])

  const error = useCallback((message: string, duration?: number) => {
    addToast('error', message, duration)
  }, [addToast])

  const warning = useCallback((message: string, duration?: number) => {
    addToast('warning', message, duration)
  }, [addToast])

  const info = useCallback((message: string, duration?: number) => {
    addToast('info', message, duration)
  }, [addToast])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  )
}

// Hook to use toast
// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

// 全局 toast 实例（用于非组件环境）
let globalToast: ToastContextValue | null = null

// eslint-disable-next-line react-refresh/only-export-components
export function setGlobalToast(toast: ToastContextValue) {
  globalToast = toast
}

// eslint-disable-next-line react-refresh/only-export-components
export const toast = {
  success: (message: string, duration?: number) => globalToast?.success(message, duration),
  error: (message: string, duration?: number) => globalToast?.error(message, duration),
  warning: (message: string, duration?: number) => globalToast?.warning(message, duration),
  info: (message: string, duration?: number) => globalToast?.info(message, duration),
}
