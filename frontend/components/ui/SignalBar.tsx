import React from 'react'
import clsx from 'clsx'

interface SignalBarProps {
  label: string
  value: number // 0 to 100 or 0 to 1
  severity?: 'low' | 'medium' | 'high'
  invertRisk?: boolean // If true, higher score is safer (e.g. Liveness)
  detail?: string
  className?: string
}

export const SignalBar: React.FC<SignalBarProps> = ({
  label,
  value,
  severity,
  invertRisk = false,
  detail,
  className,
}) => {
  const normalizedValue = value <= 1.0 ? Math.round(value * 100) : Math.min(100, Math.round(value))

  // Determine bar fill color
  let barColor = 'bg-white'
  if (severity) {
    if (severity === 'low') barColor = invertRisk ? 'bg-status-danger' : 'bg-status-safe'
    if (severity === 'medium') barColor = 'bg-status-warning'
    if (severity === 'high') barColor = invertRisk ? 'bg-status-safe' : 'bg-status-danger'
  } else {
    if (normalizedValue >= 75) barColor = invertRisk ? 'bg-status-safe' : 'bg-status-danger'
    else if (normalizedValue >= 40) barColor = 'bg-status-warning'
    else barColor = invertRisk ? 'bg-status-danger' : 'bg-status-safe'
  }

  return (
    <div className={clsx('space-y-1.5', className)}>
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-white/80">{label}</span>
        <span className="font-mono text-white/60">{normalizedValue}%</span>
      </div>
      <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden backdrop-blur-sm">
        <div
          className={clsx('h-full rounded-full transition-all duration-500 ease-out', barColor)}
          style={{ width: `${normalizedValue}%` }}
        />
      </div>
      {detail && (
        <p className="text-[11px] text-white/40 leading-snug">{detail}</p>
      )}
    </div>
  )
}

export default SignalBar
