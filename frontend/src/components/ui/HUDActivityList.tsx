/**
 * HUD 风格活动列表组件
 * HUD-style Activity List Component
 *
 * 用于展示实时活动和状态
 */

import { CheckCircle, XCircle, Loader2, Circle } from 'lucide-react'

interface ActivityItem {
  id: string
  name: string
  status: 'success' | 'error' | 'running' | 'pending'
  time?: string
  detail?: string
  value?: string | number
}

interface HUDActivityListProps {
  items: ActivityItem[]
  maxItems?: number
  className?: string
  emptyText?: string
}

const statusConfig = {
  success: {
    icon: CheckCircle,
    color: 'text-emerald-400',
    dot: 'bg-emerald-400',
    glow: 'shadow-[0_0_8px_rgba(16,185,129,0.5)]',
  },
  error: {
    icon: XCircle,
    color: 'text-red-400',
    dot: 'bg-red-400',
    glow: 'shadow-[0_0_8px_rgba(239,68,68,0.5)]',
  },
  running: {
    icon: Loader2,
    color: 'text-blue-400',
    dot: 'bg-blue-400 animate-pulse',
    glow: 'shadow-[0_0_8px_rgba(59,130,246,0.5)]',
  },
  pending: {
    icon: Circle,
    color: 'text-slate-500',
    dot: 'bg-slate-500',
    glow: '',
  },
}

export default function HUDActivityList({
  items,
  maxItems = 5,
  className = '',
  emptyText = '暂无活动',
}: HUDActivityListProps) {
  const displayItems = items.slice(0, maxItems)

  if (displayItems.length === 0) {
    return (
      <div className={`text-center py-8 text-slate-500 ${className}`}>
        {emptyText}
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {displayItems.map((item, index) => {
        const status = statusConfig[item.status]

        return (
          <div
            key={item.id}
            className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition-colors"
            style={{
              animation: `fadeInUp 0.3s ease-out ${index * 0.05}s both`,
            }}
          >
            {/* 状态指示器 */}
            <div className="relative">
              <div className={`w-2 h-2 rounded-full ${status.dot} ${status.glow}`} />
            </div>

            {/* 内容 */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-200 truncate">
                  {item.name}
                </span>
                {item.status === 'running' && (
                  <Loader2 className="w-3 h-3 text-blue-400 animate-spin" />
                )}
              </div>
              {item.detail && (
                <p className="text-xs text-slate-500 truncate">{item.detail}</p>
              )}
            </div>

            {/* 时间/数值 */}
            <div className="flex items-center gap-3 text-xs">
              {item.time && (
                <span className="text-slate-500">{item.time}</span>
              )}
              {item.value !== undefined && (
                <span className={`font-mono ${status.color}`}>
                  {item.status === 'success' && '+'}
                  {item.value}
                </span>
              )}
            </div>
          </div>
        )
      })}

      <style>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  )
}
