import React from 'react'
import clsx from 'clsx'

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'base' | 'elevated' | 'floating' | 'interactive'
  glow?: 'none' | 'blue' | 'violet' | 'safe'
  children: React.ReactNode
  className?: string
}

export const GlassCard: React.FC<GlassCardProps> = ({
  variant = 'base',
  glow = 'none',
  children,
  className,
  ...props
}) => {
  const variantStyles = {
    base: 'glass-surface',
    elevated: 'glass-card',
    floating: 'glass-floating',
    interactive: 'glass-card-interactive',
  }[variant]

  const glowStyles = {
    none: '',
    blue: 'shadow-[0_0_25px_rgba(255,255,255,0.18)] border-white/30',
    violet: 'shadow-[0_0_25px_rgba(212,212,216,0.15)] border-white/25',
    safe: 'shadow-glow-safe border-status-safe/30',
  }[glow]

  return (
    <div
      className={clsx(
        variantStyles,
        glowStyles,
        'relative overflow-hidden p-6',
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export default GlassCard
