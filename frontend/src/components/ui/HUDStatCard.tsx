/**
 * HUD 风格统计卡片组件
 * HUD-style Stat Card Component
 *
 * 科幻风格的统计卡片，带有发光边框和脉冲动画
 */

import { ReactNode } from 'react'
import { Loader2 } from 'lucide-react'

interface HUDStatCardProps {
  title: string
  value: number | string
  suffix?: string
  icon?: ReactNode
  color?: 'purple' | 'blue' | 'green' | 'cyan' | 'pink' | 'orange'
  trend?: {
    value: number
    label: string
  }
  loading?: boolean
  className?: string
}

// 颜色配置
const colorConfig = {
  purple: {
    border: 'border-purple-500/30',
    glow: 'shadow-[0_0_20px_rgba(168,85,247,0.2)]',
    text: 'text-purple-400',
    icon: 'bg-purple-500/20 text-purple-400',
    bar: 'bg-purple-500',
  },
  blue: {
    border: 'border-blue-500/30',
    glow: 'shadow-[0_0_20px_rgba(59,130,246,0.2)]',
    text: 'text-blue-400',
    icon: 'bg-blue-500/20 text-blue-400',
    bar: 'bg-blue-500',
  },
  green: {
    border: 'border-emerald-500/30',
    glow: 'shadow-[0_0_20px_rgba(16,185,129,0.2)]',
    text: 'text-emerald-400',
    icon: 'bg-emerald-500/20 text-emerald-400',
    bar: 'bg-emerald-500',
  },
  cyan: {
    border: 'border-cyan-500/30',
    glow: 'shadow-[0_0_20px_rgba(6,182,212,0.2)]',
    text: 'text-cyan-400',
    icon: 'bg-cyan-500/20 text-cyan-400',
    bar: 'bg-cyan-500',
  },
  pink: {
    border: 'border-pink-500/30',
    glow: 'shadow-[0_0_20px_rgba(236,72,153,0.2)]',
    text: 'text-pink-400',
    icon: 'bg-pink-500/20 text-pink-400',
    bar: 'bg-pink-500',
  },
  orange: {
    border: 'border-orange-500/30',
    glow: 'shadow-[0_0_20px_rgba(249,115,22,0.2)]',
    text: 'text-orange-400',
    icon: 'bg-orange-500/20 text-orange-400',
    bar: 'bg-orange-500',
  },
}

export default function HUDStatCard({
  title,
  value,
  suffix,
  icon,
  color = 'cyan',
  trend,
  loading = false,
  className = '',
}: HUDStatCardProps) {
  const colors = colorConfig[color]

  return (
    <div
      className={`
        relative overflow-hidden rounded-xl
        bg-slate-900/80 backdrop-blur-sm
        border ${colors.border}
        ${colors.glow}
        transition-all duration-300
        hover:${colors.glow.replace('0.2', '0.3')}
        ${className}
      `}
    >
      {/* 扫描线动画效果 */}
      <div className="absolute inset-0 opacity-10">
        <div
          className="absolute inset-0 bg-gradient-to-b from-transparent via-white/5 to-transparent"
          style={{
            animation: 'scanline 4s linear infinite',
          }}
        />
      </div>

      {/* 角落装饰 */}
      <div className={`absolute top-0 left-0 w-4 h-4 border-l-2 border-t-2 ${colors.border}`} />
      <div className={`absolute top-0 right-0 w-4 h-4 border-r-2 border-t-2 ${colors.border}`} />
      <div className={`absolute bottom-0 left-0 w-4 h-4 border-l-2 border-b-2 ${colors.border}`} />
      <div className={`absolute bottom-0 right-0 w-4 h-4 border-r-2 border-b-2 ${colors.border}`} />

      <div className="relative p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-medium tracking-wider text-slate-400 uppercase">
              {title}
            </p>
            <div className="mt-2 flex items-baseline gap-1">
              {loading ? (
                <Loader2 className={`w-8 h-8 animate-spin ${colors.text}`} />
              ) : (
                <>
                  <span className={`text-3xl font-bold font-mono ${colors.text}`}>
                    {typeof value === 'number' ? value.toLocaleString() : value}
                  </span>
                  {suffix && (
                    <span className="text-sm text-slate-500">{suffix}</span>
                  )}
                </>
              )}
            </div>
            {trend && (
              <p className={`mt-1 text-xs ${trend.value >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {trend.value >= 0 ? '+' : ''}{trend.value}% {trend.label}
              </p>
            )}
          </div>
          {icon && (
            <div className={`p-2.5 rounded-lg ${colors.icon}`}>
              {icon}
            </div>
          )}
        </div>

        {/* 底部进度条装饰 */}
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-slate-800">
          <div
            className={`h-full ${colors.bar} animate-pulse`}
            style={{ width: '60%' }}
          />
        </div>
      </div>

      <style>{`
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100%); }
        }
      `}</style>
    </div>
  )
}
