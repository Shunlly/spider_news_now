/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // HUD Design System - 字体配置
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
        geist: ['Geist', 'sans-serif'],
        'space-grotesk': ['Space Grotesk', 'sans-serif'],
      },
      // HUD Design System - 自定义颜色
      colors: {
        // HUD 背景色
        'hud-bg': '#0a0a0f',
        'hud-bg-dark': '#050508',
        // HUD 主色调 - 青色
        'hud-cyan': {
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
        },
        // HUD 紫色
        'hud-purple': {
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
        },
        // HUD 边框色
        'hud-border': 'rgba(148, 163, 184, 0.2)',
        'hud-border-hover': 'rgba(6, 182, 212, 0.3)',
      },
      // HUD Design System - 圆角
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },
      // HUD Design System - 发光阴影
      boxShadow: {
        // HUD 青色发光
        'hud-cyan-sm': '0 0 10px rgba(6, 182, 212, 0.2)',
        'hud-cyan': '0 0 15px rgba(6, 182, 212, 0.3)',
        'hud-cyan-lg': '0 0 25px rgba(6, 182, 212, 0.4)',
        // HUD 紫色发光
        'hud-purple-sm': '0 0 10px rgba(168, 85, 247, 0.2)',
        'hud-purple': '0 0 15px rgba(168, 85, 247, 0.3)',
        'hud-purple-lg': '0 0 25px rgba(168, 85, 247, 0.4)',
        // HUD 蓝色发光
        'hud-blue-sm': '0 0 10px rgba(59, 130, 246, 0.2)',
        'hud-blue': '0 0 15px rgba(59, 130, 246, 0.3)',
        'hud-blue-lg': '0 0 25px rgba(59, 130, 246, 0.4)',
        // HUD 绿色发光
        'hud-green-sm': '0 0 10px rgba(16, 185, 129, 0.2)',
        'hud-green': '0 0 15px rgba(16, 185, 129, 0.3)',
        'hud-green-lg': '0 0 25px rgba(16, 185, 129, 0.4)',
        // HUD 红色发光
        'hud-red-sm': '0 0 10px rgba(239, 68, 68, 0.2)',
        'hud-red': '0 0 15px rgba(239, 68, 68, 0.3)',
        'hud-red-lg': '0 0 25px rgba(239, 68, 68, 0.4)',
        // HUD 黄色发光
        'hud-yellow-sm': '0 0 10px rgba(234, 179, 8, 0.2)',
        'hud-yellow': '0 0 15px rgba(234, 179, 8, 0.3)',
        'hud-yellow-lg': '0 0 25px rgba(234, 179, 8, 0.4)',
      },
      // HUD Design System - 背景渐变
      backgroundImage: {
        'hud-gradient': 'linear-gradient(to right, #06b6d4, #a855f7)',
        'hud-gradient-purple': 'linear-gradient(to right, #9333ea, #3b82f6)',
        'hud-gradient-cyan': 'linear-gradient(to right, #06b6d4, #22d3ee)',
      },
      // HUD 动画
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'fade-in-up': 'fadeInUp 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'glow-pulse-cyan': 'glowPulseCyan 2s ease-in-out infinite',
        'scan-line': 'scanLine 3s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 15px rgba(168, 85, 247, 0.2)' },
          '50%': { boxShadow: '0 0 25px rgba(168, 85, 247, 0.4)' },
        },
        glowPulseCyan: {
          '0%, 100%': { boxShadow: '0 0 15px rgba(6, 182, 212, 0.2)' },
          '50%': { boxShadow: '0 0 25px rgba(6, 182, 212, 0.4)' },
        },
        scanLine: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
      // HUD 背景模糊
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
