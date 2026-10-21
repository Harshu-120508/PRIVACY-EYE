import React from 'react'
import clsx from 'clsx'

export interface TabItem {
  id: string
  label: string
  icon?: React.ReactNode
  badge?: string | number
}

interface GlassTabsProps {
  tabs: TabItem[]
  activeTab: string
  onChange: (id: string) => void
  className?: string
}

export const GlassTabs: React.FC<GlassTabsProps> = ({
  tabs,
  activeTab,
  onChange,
  className,
}) => {
  return (
    <div
      className={clsx(
        'inline-flex items-center p-1.5 rounded-2xl glass-surface border border-white/10 backdrop-blur-xl',
        className
      )}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={clsx(
              'relative flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition-all duration-200 select-none',
              isActive
                ? 'text-white bg-white/10 shadow-sm border border-white/15'
                : 'text-white/50 hover:text-white/80 hover:bg-white/5 border border-transparent'
            )}
          >
            {tab.icon && <span className="w-3.5 h-3.5 flex-shrink-0">{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={clsx(
                  'text-[10px] px-1.5 py-0.2 rounded-full font-mono',
                  isActive ? 'bg-white text-black font-bold' : 'bg-white/10 text-white/60'
                )}
              >
                {tab.badge}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

export default GlassTabs
