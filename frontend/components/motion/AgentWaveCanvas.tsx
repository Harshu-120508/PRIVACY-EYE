'use client'
import React, { useEffect, useRef } from 'react'

interface AgentWaveCanvasProps {
  className?: string
  opacity?: number
  speed?: number
  amplitude?: number
}

/**
 * Lightweight 60fps monochrome wave ribbon backdrop inspired by MotionSites Agent Wave.
 * Automatically draws a single static wave frame when prefers-reduced-motion is enabled.
 */
export const AgentWaveCanvas: React.FC<AgentWaveCanvasProps> = ({
  className = '',
  opacity = 0.5,
  speed = 0.014,
  amplitude = 38,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let animId = 0
    let phase = 0
    let width = 0
    let height = 0

    const resize = () => {
      const parent = canvas.parentElement
      if (!parent) return
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      width = parent.clientWidth
      height = parent.clientHeight
      canvas.width = width * dpr
      canvas.height = height * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    const drawFrame = () => {
      if (!width || !height) return
      ctx.clearRect(0, 0, width, height)

      const waves = [
        { freq: 0.0042, amp: amplitude * 1.1, phaseMult: 1.0, alpha: 0.28, lineWidth: 1.5, yOffset: 0 },
        { freq: 0.0058, amp: amplitude * 0.78, phaseMult: -1.3, alpha: 0.18, lineWidth: 1.1, yOffset: 16 },
        { freq: 0.0031, amp: amplitude * 1.35, phaseMult: 0.65, alpha: 0.11, lineWidth: 1.0, yOffset: -14 },
        { freq: 0.0075, amp: amplitude * 0.45, phaseMult: 1.6, alpha: 0.14, lineWidth: 0.9, yOffset: 6 },
      ]

      const centerY = height * 0.56

      for (const w of waves) {
        const grad = ctx.createLinearGradient(0, 0, width, 0)
        grad.addColorStop(0, 'rgba(255, 255, 255, 0)')
        grad.addColorStop(0.25, `rgba(255, 255, 255, ${w.alpha * 0.85})`)
        grad.addColorStop(0.5, `rgba(255, 255, 255, ${w.alpha * 1.35})`)
        grad.addColorStop(0.75, `rgba(228, 228, 231, ${w.alpha * 0.85})`)
        grad.addColorStop(1, 'rgba(255, 255, 255, 0)')

        ctx.beginPath()
        ctx.strokeStyle = grad
        ctx.lineWidth = w.lineWidth

        for (let x = 0; x <= width; x += 6) {
          const envelope = Math.sin((x / width) * Math.PI)
          const y =
            centerY +
            w.yOffset +
            Math.sin(x * w.freq + phase * w.phaseMult) * w.amp * envelope +
            Math.cos(x * w.freq * 0.5 - phase * 0.6) * (w.amp * 0.35) * envelope
          if (x === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        }
        ctx.stroke()
      }
    }

    const tick = () => {
      phase += speed
      drawFrame()
      if (!reducedMotion) {
        animId = requestAnimationFrame(tick)
      }
    }

    resize()
    drawFrame()
    if (!reducedMotion) {
      animId = requestAnimationFrame(tick)
    }

    const ro = new ResizeObserver(() => {
      resize()
      drawFrame()
    })
    if (canvas.parentElement) ro.observe(canvas.parentElement)

    return () => {
      cancelAnimationFrame(animId)
      ro.disconnect()
    }
  }, [amplitude, speed])

  return (
    <div
      className={`pointer-events-none overflow-hidden ${className}`}
      style={{ opacity }}
      aria-hidden="true"
    >
      <canvas ref={canvasRef} className="block h-full w-full" />
    </div>
  )
}
