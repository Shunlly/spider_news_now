/**
 * HUD 风格面板组件
 * HUD-style Panel Component
 *
 * 带有网格背景和发光边框的面板
 */

import { ReactNode } from 'react'

interface HUDPanelProps {
  title?: string
  subtitle?: string
  children: ReactNode
  color?: 'purple' | 'blue' | 'green' | 'cyan'
  className?: string
  headerAction?: ReactNode
}

const colorConfig = {
  purple: {
    border: 'border-purple-500/20',
    title: 'text-purple-400',
    glow: 'shadow-[0_0_30px_rgba(168,85,247,0.1)]',
  },
  blue: {
    border: 'border-blue-500/20',
    title: 'text-blue-400',
    glow: 'shadow-[0_0_30px_rgba(59,130,246,0.1)]',
  },
  green: {
    border: 'border-emerald-500/20',
    title: 'text-emerald-400',
    glow: 'shadow-[0_0_30px_rgba(16,185,129,0.1)]',
  },
  cyan: {
    border: 'border-cyan-500/20',
    title: 'text-cyan-400',
    glow: 'shadow-[0_0_30px_rgba(6,182,212,0.1)]',
  },
}

export default function HUDPanel({
  title,
  subtitle,
  children,
  color = 'cyan',
  className = '',
  headerAction,
}: HUDPanelProps) {
  const colors = colorConfig[color]

  return (
    <div
      className={`
        relative overflow-hidden rounded-xl
        bg-slate-900/80 backdrop-blur-sm
        border ${colors.border}
        ${colors.glow}
        ${className}
      `}
    >
      {/* 网格背景 */}
      <div
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px',
        }}
      />

      {/* 角落装饰 */}
      <div className={`absolute top-0 left-0 w-6 h-6 border-l-2 border-t-2 ${colors.border}`} />
      <div className={`absolute top-0 right-0 w-6 h-6 border-r-2 border-t-2 ${colors.border}`} />
      <div className={`absolute bottom-0 left-0 w-6 h-6 border-l-2 border-b-2 ${colors.border}`} />
      <div className={`absolute bottom-0 right-0 w-6 h-6 border-r-2 border-b-2 ${colors.border}`} />

      {/* 标题区域 */}
      {title && (
        <div className="relative flex items-center justify-between px-5 py-4 border-b border-slate-800/50">
          <div>
            <h3 className={`text-sm font-semibold tracking-wider uppercase ${colors.title}`}>
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>
            )}
          </div>
          {headerAction}
        </div>
      )}

      {/* 内容区域 */}
      <div className="relative p-5">
        {children}
      </div>
    </div>
  )
}
