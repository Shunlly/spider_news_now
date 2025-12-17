/**
 * 懒加载图片组件
 * Lazy Loading Image Component
 *
 * 功能：
 * - 视口检测懒加载
 * - 加载占位符
 * - 错误处理
 * - 支持 WebP 回退
 */

import { useState, useRef, useEffect, ImgHTMLAttributes } from 'react'
import { ImageOff } from 'lucide-react'
import clsx from 'clsx'

interface LazyImageProps extends Omit<ImgHTMLAttributes<HTMLImageElement>, 'onLoad' | 'onError'> {
  /** 图片源 */
  src: string
  /** 替代文本 */
  alt: string
  /** 占位符颜色 */
  placeholderColor?: string
  /** 加载失败时显示的图标 */
  showErrorIcon?: boolean
  /** 自定义类名 */
  className?: string
  /** 容器类名 */
  containerClassName?: string
}

export default function LazyImage({
  src,
  alt,
  placeholderColor = 'bg-stone-100',
  showErrorIcon = true,
  className,
  containerClassName,
  ...props
}: LazyImageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [isError, setIsError] = useState(false)
  const [isInView, setIsInView] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // 使用 IntersectionObserver 检测是否在视口内
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (entry && entry.isIntersecting) {
          setIsInView(true)
          observer.disconnect()
        }
      },
      {
        rootMargin: '50px', // 提前 50px 开始加载
        threshold: 0,
      }
    )

    if (containerRef.current) {
      observer.observe(containerRef.current)
    }

    return () => observer.disconnect()
  }, [])

  const handleLoad = () => {
    setIsLoaded(true)
    setIsError(false)
  }

  const handleError = () => {
    setIsError(true)
    setIsLoaded(true)
  }

  return (
    <div
      ref={containerRef}
      className={clsx(
        'relative overflow-hidden',
        containerClassName
      )}
    >
      {/* 占位符 */}
      {!isLoaded && (
        <div
          className={clsx(
            'absolute inset-0 animate-pulse',
            placeholderColor
          )}
        />
      )}

      {/* 错误状态 */}
      {isError && showErrorIcon && (
        <div className="absolute inset-0 flex items-center justify-center bg-stone-100">
          <ImageOff className="w-8 h-8 text-stone-300" />
        </div>
      )}

      {/* 图片 */}
      {isInView && !isError && (
        <img
          ref={imgRef}
          src={src}
          alt={alt}
          onLoad={handleLoad}
          onError={handleError}
          className={clsx(
            'transition-opacity duration-300',
            isLoaded ? 'opacity-100' : 'opacity-0',
            className
          )}
          loading="lazy"
          decoding="async"
          {...props}
        />
      )}
    </div>
  )
}

/**
 * 响应式图片组件
 * 支持不同屏幕尺寸加载不同图片
 */
interface ResponsiveImageProps extends LazyImageProps {
  /** 小屏幕图片 */
  srcSmall?: string
  /** 中屏幕图片 */
  srcMedium?: string
  /** 大屏幕图片 */
  srcLarge?: string
}

export function ResponsiveImage({
  src,
  srcSmall,
  srcMedium,
  srcLarge,
  alt,
  ...props
}: ResponsiveImageProps) {
  return (
    <picture>
      {srcLarge && <source media="(min-width: 1024px)" srcSet={srcLarge} />}
      {srcMedium && <source media="(min-width: 768px)" srcSet={srcMedium} />}
      {srcSmall && <source media="(min-width: 480px)" srcSet={srcSmall} />}
      <LazyImage src={src} alt={alt} {...props} />
    </picture>
  )
}
