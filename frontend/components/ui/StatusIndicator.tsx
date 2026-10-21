import React from 'react'
import clsx from 'clsx'

interface StatusIndicatorProps {
  status: 'safe' | 'warning' | 'danger' | 'undetermined' | 'active'
  label?: string
  sublabel?: string
  className?: string
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  sublabel,
  className,
}) => {
  const dotColor = {
    safe: 'bg-status-safe shadow-[0_0_10px_#4ADE80]',
    active: 'bg-white shadow-[0_0_10px_#FFFFFF]',
    warning: 'bg-status-warning shadow-[0_0_10px_#FBBF24]',
    danger: 'bg-status-danger shadow-[0_0_10px_#FB7185]',
    undetermined: 'bg-status-undetermined shadow-[0_0_8px_#94A3B8]',
  }[status]

  return (
    <div className={clsx('inline-flex items-center gap-2', className)}>
      <span className="relative flex h-2.5 w-2.5">
        <span
          className={clsx(
            'animate-ping absolute inline-flex h-full w-full rounded-full opacity-60',
            dotColor
          )}
        />
        <span className={clsx('relative inline-flex rounded-full h-2.5 w-2.5', dotColor)} />
      </span>
      {label && (
        <div className="flex flex-col">
          <span className="text-xs font-semibold tracking-wide text-white uppercase">{label}</span>
          {sublabel && (
            <span className="text-[11px] text-white/50">{sublabel}</span>
          )}
        </div>
      )}
    </div>
  )
}

export default StatusIndicator
