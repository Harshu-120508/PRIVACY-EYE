import React from 'react'

export const AmbientBackground: React.FC = () => {
  return (
    <div className="ambient-glow" aria-hidden="true">
      {/* Dynamic ambient radial gradients - High-contrast monochrome rim lighting */}
      <div className="absolute top-[-10%] left-[-5%] w-[45vw] h-[45vw] rounded-full bg-white/[0.025] blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[50vw] h-[50vw] rounded-full bg-white/[0.02] blur-[140px] pointer-events-none" />
      <div className="absolute top-[40%] right-[20%] w-[35vw] h-[35vw] rounded-full bg-white/[0.015] blur-[100px] pointer-events-none" />
    </div>
  )
}

export default AmbientBackground
