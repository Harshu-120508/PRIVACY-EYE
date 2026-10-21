import React from 'react'
import clsx from 'clsx'

export type RingStatus = 'safe' | 'warning' | 'danger' | 'brand' | 'undetermined'

interface ConfidenceRingProps {
  value: number
  size?: number
  strokeWidth?: number
  label?: string
  status?: RingStatus | 'auto'
  className?: string
}

export const ConfidenceRing: React.FC<ConfidenceRingProps> = ({
  value,
  size = 120,
  strokeWidth = 9,
  label = 'CONFIDENCE',
  status = 'auto',
  className,
}) => {
  const clamped = Math.max(0, Math.min(100, Math.round(value)))
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (clamped / 100) * circumference

  let resolvedStatus: RingStatus = 'safe'
  if (status === 'auto') {
    if (clamped >= 80) resolvedStatus = 'safe'
    else if (clamped >= 60) resolvedStatus = 'warning'
    else resolvedStatus = 'danger'
  } else {
    resolvedStatus = status
  }

  const strokeColor: Record<RingStatus, string> = {
    safe: '#4ADE80',
    warning: '#FBBF24',
    danger: '#FB7185',
    brand: '#FFFFFF',
    undetermined: '#94A3B8',
  }

  const glowClass: Record<RingStatus, string> = {
    safe: 'drop-shadow-[0_0_8px_rgba(74,222,128,0.4)]',
    warning: 'drop-shadow-[0_0_8px_rgba(251,191,36,0.4)]',
    danger: 'drop-shadow-[0_0_8px_rgba(251,113,133,0.4)]',
    brand: 'drop-shadow-[0_0_8px_rgba(255,255,255,0.4)]',
    undetermined: 'drop-shadow-[0_0_6px_rgba(148,163,184,0.3)]',
  }

  return (
    <div
      className={clsx('relative inline-flex flex-col items-center justify-center', className)}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        {/* Background Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255, 255, 255, 0.08)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Dynamic Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={strokeColor[resolvedStatus]}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          fill="none"
          className={clsx('transition-all duration-500 ease-out', glowClass[resolvedStatus])}
        />
      </svg>
      {/* Central Content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-2xl font-bold font-mono tracking-tight text-white">
          {clamped}%
        </span>
        {label && (
          <span className="text-[10px] uppercase font-semibold tracking-wider text-white/50 -mt-0.5">
            {label}
          </span>
        )}
      </div>
    </div>
  )
}

export default ConfidenceRing
