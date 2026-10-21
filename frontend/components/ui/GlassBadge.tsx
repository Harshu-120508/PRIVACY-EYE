import React from 'react'
import clsx from 'clsx'

export type BadgeStatus = 'safe' | 'warning' | 'danger' | 'undetermined' | 'brand' | 'neutral'

interface GlassBadgeProps {
  status?: BadgeStatus
  label: string
  pulse?: boolean
  icon?: React.ReactNode
  className?: string
}

export const GlassBadge: React.FC<GlassBadgeProps> = ({
  status = 'neutral',
  label,
  pulse = false,
  icon,
  className,
}) => {
  const statusStyles: Record<BadgeStatus, { wrapper: string; dot: string }> = {
    safe: {
      wrapper: 'badge-safe',
      dot: 'bg-status-safe shadow-[0_0_8px_#4ADE80]',
    },
    warning: {
      wrapper: 'badge-warning',
      dot: 'bg-status-warning shadow-[0_0_8px_#FBBF24]',
    },
    danger: {
      wrapper: 'badge-danger',
      dot: 'bg-status-danger shadow-[0_0_8px_#FB7185]',
    },
    undetermined: {
      wrapper: 'badge-undetermined',
      dot: 'bg-status-undetermined',
    },
    brand: {
      wrapper: 'bg-white/10 border border-white/25 text-white',
      dot: 'bg-white shadow-[0_0_8px_#FFFFFF]',
    },
    neutral: {
      wrapper: 'bg-white/5 border border-white/10 text-white/70',
      dot: 'bg-white/40',
    },
  }

  const current = statusStyles[status]

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium tracking-wide transition-all backdrop-blur-md',
        current.wrapper,
        className
      )}
    >
      {pulse ? (
        <span className="relative flex h-2 w-2">
          <span
            className={clsx(
              'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
              current.dot
            )}
          />
          <span className={clsx('relative inline-flex rounded-full h-2 w-2', current.dot)} />
        </span>
      ) : icon ? (
        <span className="flex-shrink-0">{icon}</span>
      ) : (
        <span className={clsx('inline-block h-1.5 w-1.5 rounded-full', current.dot)} />
      )}
      <span>{label}</span>
    </span>
  )
}

export default GlassBadge
