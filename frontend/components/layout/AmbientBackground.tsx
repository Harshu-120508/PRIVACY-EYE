import React from 'react'

export const AmbientBackground: React.FC = () => {
  return (
    <div className="ambient-glow" aria-hidden="true">
      {/* Restrained 2D ambient radial glows using CSS gradients (GPU performant, zero filter blur) */}
      <div
        className="absolute top-[-10%] left-[5%] w-[45vw] h-[45vw] max-w-[650px] max-h-[650px] rounded-full pointer-events-none opacity-40"
        style={{
          background: 'radial-gradient(circle, rgba(19, 210, 232, 0.12) 0%, rgba(19, 210, 232, 0.02) 45%, transparent 70%)',
        }}
      />
      <div
        className="absolute bottom-[-10%] right-[5%] w-[45vw] h-[45vw] max-w-[650px] max-h-[650px] rounded-full pointer-events-none opacity-30"
        style={{
          background: 'radial-gradient(circle, rgba(192, 16, 237, 0.10) 0%, rgba(192, 16, 237, 0.02) 45%, transparent 70%)',
        }}
      />
    </div>
  )
}

export default AmbientBackground
