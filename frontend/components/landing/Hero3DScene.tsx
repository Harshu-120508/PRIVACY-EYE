'use client'
import React, { useRef, useState, useEffect } from 'react'
import Link from 'next/link'
import { motion, useMotionValue, useSpring, useTransform, useScroll } from 'framer-motion'
import {
  Camera,
  UploadCloud,
  ShieldCheck,
  Eye,
  Activity,
  Layers,
  Sparkles,
  Lock,
  ArrowRight,
  Cpu,
  CheckCircle2,
} from 'lucide-react'
import { GlassBadge } from '@/components/ui/GlassBadge'

export const Hero3DScene: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null)

  // Mouse motion values normalized to [-0.5, 0.5]
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)

  // Smooth Apple-like spring physics
  const springConfig = { stiffness: 100, damping: 22, mass: 0.8 }
  const smoothMouseX = useSpring(mouseX, springConfig)
  const smoothMouseY = useSpring(mouseY, springConfig)

  // Track window mouse movement
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window
      const x = (e.clientX / innerWidth) - 0.5
      const y = (e.clientY / innerHeight) - 0.5
      mouseX.set(x)
      mouseY.set(y)
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [mouseX, mouseY])

  // Scroll tracking for 3D fly-through dispersion
  const { scrollYProgress } = useScroll()
  const scrollSpread = useTransform(scrollYProgress, [0, 0.4], [0, 1])

  // 3D Tilt angles for the entire scene
  const sceneRotateX = useTransform(smoothMouseY, [-0.5, 0.5], [14, -14])
  const sceneRotateY = useTransform(smoothMouseX, [-0.5, 0.5], [-18, 18])

  // Individual card parallax transforms (Multi-depth layers)
  // Central Card
  const centerTranslateZ = useTransform(scrollSpread, [0, 1], [90, 200])
  const centerScale = useTransform(scrollSpread, [0, 1], [1, 0.88])
  const centerRotateX = useTransform(smoothMouseY, [-0.5, 0.5], [8, -8])
  const centerRotateY = useTransform(smoothMouseX, [-0.5, 0.5], [-10, 10])

  // Card 1: Top Left (YuNet)
  const card1X = useTransform(smoothMouseX, [-0.5, 0.5], [-30, 20])
  const card1Y = useTransform(smoothMouseY, [-0.5, 0.5], [-25, 20])
  const card1SpreadX = useTransform(scrollSpread, [0, 1], [0, -180])
  const card1SpreadY = useTransform(scrollSpread, [0, 1], [0, -120])
  const card1RotX = useTransform(smoothMouseY, [-0.5, 0.5], [-12, -26])
  const card1RotY = useTransform(smoothMouseX, [-0.5, 0.5], [20, 36])

  // Card 2: Top Right (Silent-Face PAD)
  const card2X = useTransform(smoothMouseX, [-0.5, 0.5], [20, -25])
  const card2Y = useTransform(smoothMouseY, [-0.5, 0.5], [-20, 25])
  const card2SpreadX = useTransform(scrollSpread, [0, 1], [0, 180])
  const card2SpreadY = useTransform(scrollSpread, [0, 1], [0, -120])
  const card2RotX = useTransform(smoothMouseY, [-0.5, 0.5], [-12, -26])
  const card2RotY = useTransform(smoothMouseX, [-0.5, 0.5], [-20, -36])

  // Card 3: Bottom Left (FaceForensics++)
  const card3X = useTransform(smoothMouseX, [-0.5, 0.5], [-25, 20])
  const card3Y = useTransform(smoothMouseY, [-0.5, 0.5], [15, -20])
  const card3SpreadX = useTransform(scrollSpread, [0, 1], [0, -190])
  const card3SpreadY = useTransform(scrollSpread, [0, 1], [0, 130])
  const card3RotX = useTransform(smoothMouseY, [-0.5, 0.5], [16, 28])
  const card3RotY = useTransform(smoothMouseX, [-0.5, 0.5], [18, 30])

  // Card 4: Bottom Right (Celeb-DF & FFHQ)
  const card4X = useTransform(smoothMouseX, [-0.5, 0.5], [20, -20])
  const card4Y = useTransform(smoothMouseY, [-0.5, 0.5], [18, -18])
  const card4SpreadX = useTransform(scrollSpread, [0, 1], [0, 190])
  const card4SpreadY = useTransform(scrollSpread, [0, 1], [0, 130])
  const card4RotX = useTransform(smoothMouseY, [-0.5, 0.5], [16, 28])
  const card4RotY = useTransform(smoothMouseX, [-0.5, 0.5], [-18, -30])

  // Floating 3D Spheres Parallax
  const orb1X = useTransform(smoothMouseX, [-0.5, 0.5], [-45, 45])
  const orb1Y = useTransform(smoothMouseY, [-0.5, 0.5], [-35, 35])
  const orb2X = useTransform(smoothMouseX, [-0.5, 0.5], [50, -50])
  const orb2Y = useTransform(smoothMouseY, [-0.5, 0.5], [40, -40])
  const orb3X = useTransform(smoothMouseX, [-0.5, 0.5], [-30, 30])
  const orb3Y = useTransform(smoothMouseY, [-0.5, 0.5], [35, -35])

  return (
    <div
      ref={containerRef}
      className="relative w-full min-h-[640px] md:min-h-[720px] flex items-center justify-center select-none overflow-visible"
      style={{ perspective: '1400px' }}
    >
      {/* ── 3D SCENE CONTAINER (Preserves 3D Space) ── */}
      <motion.div
        className="relative w-full max-w-5xl h-[580px] flex items-center justify-center"
        style={{
          transformStyle: 'preserve-3d',
          rotateX: sceneRotateX,
          rotateY: sceneRotateY,
        }}
      >
        {/* ── ARCHITECTURAL CYBERSECURITY 3D GRID BACKGROUND (Behind Cards) ── */}
        <div
          className="absolute inset-[-40px] rounded-4xl border border-white/[0.07] pointer-events-none opacity-40"
          style={{
            transform: 'translateZ(-140px)',
            backgroundImage:
              'linear-gradient(to right, rgba(255, 255, 255, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.05) 1px, transparent 1px)',
            backgroundSize: '54px 54px',
            maskImage: 'radial-gradient(ellipse at center, rgba(0,0,0,1) 40%, transparent 80%)',
            WebkitMaskImage: 'radial-gradient(ellipse at center, rgba(0,0,0,1) 40%, transparent 80%)',
          }}
        />

        {/* ── AMBIENT SPECULAR GROUND SHADOW (Simulating Floor Light) ── */}
        <div
          className="absolute bottom-[-60px] w-[80%] h-32 rounded-full bg-black/80 blur-3xl pointer-events-none"
          style={{ transform: 'translateZ(-120px) rotateX(75deg)' }}
        />

        {/* ── FLOATING 3D SPHERES / BIOMETRIC NODES (Multi-Depth) ── */}
        {/* Orb 1: Upper Left Floating Glass Orb (Monochrome Porcelain) */}
        <motion.div
          className="absolute left-[8%] top-[14%] w-14 h-14 rounded-full pointer-events-none"
          style={{
            x: orb1X,
            y: orb1Y,
            transform: 'translateZ(130px)',
            background:
              'radial-gradient(circle at 35% 35%, #FFFFFF, #E4E4E7 40%, #18181B 85%)',
            boxShadow: '0 20px 40px rgba(0,0,0,0.85), 0 0 25px rgba(255, 255, 255, 0.25)',
            border: '1px solid rgba(255, 255, 255, 0.35)',
          }}
        />

        {/* Orb 2: Lower Right Sculpted Platinum Orb */}
        <motion.div
          className="absolute right-[6%] bottom-[12%] w-20 h-20 rounded-full pointer-events-none"
          style={{
            x: orb2X,
            y: orb2Y,
            transform: 'translateZ(160px)',
            background:
              'radial-gradient(circle at 30% 30%, #FFFFFF, #D4D4D8 35%, #52525B 70%, #000000 95%)',
            boxShadow: '0 24px 50px rgba(0,0,0,0.85), 0 0 30px rgba(255, 255, 255, 0.18)',
            border: '1px solid rgba(255, 255, 255, 0.25)',
          }}
        />

        {/* Orb 3: Micro Light Node Near Center */}
        <motion.div
          className="absolute left-[34%] bottom-[8%] w-8 h-8 rounded-full pointer-events-none"
          style={{
            x: orb3X,
            y: orb3Y,
            transform: 'translateZ(70px)',
            background:
              'radial-gradient(circle at 35% 35%, #FFFFFF, #A1A1AA 60%, #0A0A0A 90%)',
            boxShadow: '0 10px 25px rgba(255, 255, 255, 0.25)',
          }}
        />

        {/* ── CARD 1: TOP LEFT (YuNet Biometrics - 3D Tilted Backwards Left) ── */}
        <motion.div
          className="absolute left-[4%] top-[4%] w-64 md:w-72 rounded-3xl p-5 border border-white/18 shadow-2xl backdrop-blur-2xl transition-shadow duration-300"
          style={{
            x: card1X,
            y: card1Y,
            translateX: card1SpreadX,
            translateY: card1SpreadY,
            transform: 'translateZ(30px)',
            rotateX: card1RotX,
            rotateY: card1RotY,
            rotateZ: -4,
            background:
              'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%)',
            boxShadow: '0 25px 60px rgba(0,0,0,0.85), inset 0 1px 0 rgba(255,255,255,0.2)',
          }}
        >
          {/* Flowing Metallic Ribbon Across Card (High-Contrast White Specular) */}
          <div
            className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-14 pointer-events-none opacity-80"
            style={{
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.12) 30%, rgba(255, 255, 255, 0.5) 50%, rgba(255, 255, 255, 0.12) 70%, transparent 100%)',
              filter: 'blur(3px)',
              transform: 'rotate(-14deg) skewX(-12deg)',
            }}
          />

          <div className="relative z-10 space-y-3 text-left">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-white/90">
                YuNet Biometrics
              </span>
              <span className="w-2 h-2 rounded-full bg-status-safe shadow-[0_0_8px_#4ADE80]" />
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-xl font-bold font-mono text-white">5-POINT TRACKING</span>
            </div>

            <p className="text-[11px] text-white/60 leading-snug">
              Continuous landmark vector tracking with smooth physiological micro-motion estimation.
            </p>

            <div className="pt-1 flex items-center gap-2 text-[10px] font-mono text-white/80">
              <CheckCircle2 className="w-3.5 h-3.5 text-status-safe" />
              <span>Organic Face Trajectory</span>
            </div>
          </div>
        </motion.div>

        {/* ── CARD 2: TOP RIGHT (Silent-Face PAD - 3D Tilted Backwards Right) ── */}
        <motion.div
          className="absolute right-[4%] top-[6%] w-64 md:w-72 rounded-3xl p-5 border border-white/18 shadow-2xl backdrop-blur-2xl transition-shadow duration-300"
          style={{
            x: card2X,
            y: card2Y,
            translateX: card2SpreadX,
            translateY: card2SpreadY,
            transform: 'translateZ(40px)',
            rotateX: card2RotX,
            rotateY: card2RotY,
            rotateZ: 4,
            background:
              'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%)',
            boxShadow: '0 25px 60px rgba(0,0,0,0.85), inset 0 1px 0 rgba(255,255,255,0.2)',
          }}
        >
          {/* Flowing Specular Ribbon */}
          <div
            className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-14 pointer-events-none opacity-80"
            style={{
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.12) 30%, rgba(255, 255, 255, 0.5) 50%, rgba(255, 255, 255, 0.12) 70%, transparent 100%)',
              filter: 'blur(3px)',
              transform: 'rotate(16deg) skewX(10deg)',
            }}
          />

          <div className="relative z-10 space-y-3 text-left">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-white/90">
                Silent-Face PAD
              </span>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-mono font-bold bg-white/10 text-white border border-white/20">
                2D-FFT SPECTRA
              </span>
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-xl font-bold font-mono text-white">FOURIER PAD ENGINE</span>
            </div>

            <p className="text-[11px] text-white/60 leading-snug">
              Dual-scale 2D-FFT frequency spectra to catch electronic moiré replay patterns.
            </p>

            <div className="pt-1 flex items-center gap-2 text-[10px] font-mono text-white/60">
              <Lock className="w-3.5 h-3.5 text-white/80" />
              <span>Anti-Presentation Attack</span>
            </div>
          </div>
        </motion.div>

        {/* ── CARD 3: BOTTOM LEFT (FaceForensics++ - Textured Terrazzo / Speckled Glass Tile) ── */}
        <motion.div
          className="absolute left-[6%] bottom-[4%] w-64 md:w-72 rounded-3xl p-5 border border-white/18 shadow-2xl backdrop-blur-2xl transition-shadow duration-300"
          style={{
            x: card3X,
            y: card3Y,
            translateX: card3SpreadX,
            translateY: card3SpreadY,
            transform: 'translateZ(50px)',
            rotateX: card3RotX,
            rotateY: card3RotY,
            rotateZ: 2,
            background:
              'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(10, 10, 10, 0.95) 100%)',
            boxShadow: '0 30px 70px rgba(0,0,0,0.85), inset 0 1px 0 rgba(255,255,255,0.2)',
          }}
        >
          {/* Speckled Terrazzo Texture */}
          <div
            className="absolute inset-0 rounded-3xl opacity-20 pointer-events-none"
            style={{
              backgroundImage:
                'radial-gradient(circle, rgba(255,255,255,0.4) 1px, transparent 1px)',
              backgroundSize: '12px 12px',
            }}
          />

          {/* Specular Curvilinear Ribbon */}
          <div
            className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-12 pointer-events-none opacity-70"
            style={{
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.12) 30%, rgba(255, 255, 255, 0.5) 50%, rgba(255, 255, 255, 0.12) 70%, transparent 100%)',
              filter: 'blur(3px)',
              transform: 'rotate(-10deg)',
            }}
          />

          <div className="relative z-10 space-y-3 text-left">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-white/50">
                Spatial Forensics
              </span>
              <span className="text-[10px] font-mono font-bold text-white">ELA / DCT</span>
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-xl font-bold font-mono text-white">DCT RESIDUAL ANALYSIS</span>
            </div>

            <p className="text-[11px] text-white/60 leading-snug">
              Discrete Cosine Transform error analysis inspecting boundary chroma and compression inconsistencies.
            </p>

            <div className="pt-1 flex items-center gap-2 text-[10px] font-mono text-status-safe">
              <Activity className="w-3.5 h-3.5" />
              <span>Chroma Gradient Inspection</span>
            </div>
          </div>
        </motion.div>

        {/* ── CARD 4: BOTTOM RIGHT (Celeb-DF & FFHQ - 3D Tilted Forwards Right) ── */}
        <motion.div
          className="absolute right-[6%] bottom-[2%] w-64 md:w-72 rounded-3xl p-5 border border-white/18 shadow-2xl backdrop-blur-2xl transition-shadow duration-300"
          style={{
            x: card4X,
            y: card4Y,
            translateX: card4SpreadX,
            translateY: card4SpreadY,
            transform: 'translateZ(55px)',
            rotateX: card4RotX,
            rotateY: card4RotY,
            rotateZ: -3,
            background:
              'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%)',
            boxShadow: '0 30px 70px rgba(0,0,0,0.85), inset 0 1px 0 rgba(255,255,255,0.2)',
          }}
        >
          {/* Specular Wave */}
          <div
            className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-14 pointer-events-none opacity-80"
            style={{
              background:
                'linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.12) 30%, rgba(255, 255, 255, 0.5) 50%, rgba(255, 255, 255, 0.12) 70%, transparent 100%)',
              filter: 'blur(3px)',
              transform: 'rotate(-20deg)',
            }}
          />

          <div className="relative z-10 space-y-3 text-left">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-white/80">
                Texture Variance
              </span>
              <span className="w-2 h-2 rounded-full bg-white shadow-[0_0_8px_#FFFFFF]" />
            </div>

            <div className="flex items-baseline gap-2">
              <span className="text-xl font-bold font-mono text-white">LAPLACIAN & GAUSSIAN</span>
            </div>

            <p className="text-[11px] text-white/60 leading-snug">
              Evaluates high-frequency gradient variance to detect synthetic GAN smoothing and diffusion blurring.
            </p>

            <div className="pt-1 flex items-center gap-2 text-[10px] font-mono text-white/50">
              <Cpu className="w-3.5 h-3.5 text-white/80" />
              <span>Edge Density Consistency</span>
            </div>
          </div>
        </motion.div>

        {/* ── CENTRAL HERO CARD: PRIVACY EYE AUTHENTICITY ENGINE ── */}
        {/* Floating proudly in the foreground with strong depth (translateZ: 90px) */}
        <motion.div
          className="relative z-30 w-full max-w-md md:max-w-lg rounded-4xl p-8 md:p-10 border border-white/20 shadow-glass-floating backdrop-blur-3xl overflow-hidden group"
          style={{
            transform: 'translateZ(90px)',
            translateZ: centerTranslateZ,
            scale: centerScale,
            rotateX: centerRotateX,
            rotateY: centerRotateY,
            background:
              'linear-gradient(135deg, rgba(12, 12, 12, 0.94) 0%, rgba(4, 4, 4, 0.98) 100%)',
            boxShadow:
              '0 35px 80px rgba(0, 0, 0, 0.95), 0 0 50px rgba(255, 255, 255, 0.05), inset 0 1px 1px rgba(255, 255, 255, 0.25)',
          }}
        >
          {/* Ambient inner radial glow (Subtle monochrome rim light) */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-white/[0.04] rounded-full blur-[80px] pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-white/[0.02] rounded-full blur-[80px] pointer-events-none" />

          {/* Micro-scanning radar sweep */}
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/[0.03] to-transparent pointer-events-none animate-scan-vertical" />

          <div className="relative z-10 flex flex-col items-center text-center space-y-6">
            {/* Top Operational Pill */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full glass-surface border border-white/12 shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-safe opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-status-safe" />
              </span>
              <span className="text-[11px] font-mono font-semibold tracking-wider text-status-safe uppercase">
                AUTHENTICITY ENGINE ACTIVE
              </span>
            </div>

            {/* Central Title (Matching Reference Typography Hierarchy) */}
            <div className="space-y-1">
              <h2 className="text-3xl md:text-4xl font-extrabold text-white tracking-tight font-sans">
                Privacy Eye Core
              </h2>
              <p className="text-xs text-white/60 font-mono">
                Real-time multi-spectral neural biometric verification
              </p>
            </div>

            {/* Central Calibrated Readout Badge */}
            <div className="p-4 rounded-3xl glass-surface border border-white/10 w-full max-w-xs space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-white/50">SYSTEM STATUS:</span>
                <span className="text-status-safe font-bold">READY FOR INGESTION</span>
              </div>
              <div className="flex items-center justify-between text-[11px] font-mono text-white/70">
                <span>PRIVACY GUARANTEE:</span>
                <span className="text-white font-semibold">EPHEMERAL RAM BUFFER</span>
              </div>
            </div>

            {/* High-Contrast Porcelain Pill Button (Matching Picture High-Contrast Style) */}
            <Link href="/dashboard/live-scan" className="w-full max-w-xs">
              <motion.button
                whileHover={{ scale: 1.04, translateY: -2 }}
                whileTap={{ scale: 0.96 }}
                className="relative w-full py-3.5 px-8 rounded-full font-bold text-sm tracking-wide text-black bg-white hover:bg-neutral-200 transition-all flex items-center justify-center gap-2.5 shadow-2xl cursor-pointer"
                style={{
                  boxShadow:
                    '0 12px 35px rgba(255, 255, 255, 0.22), inset 0 1px 1px rgba(255, 255, 255, 0.8)',
                  border: '1px solid #FFFFFF',
                }}
              >
                <Camera className="w-4 h-4 text-black" />
                <span>Start Live Scan</span>
                <ArrowRight className="w-3.5 h-3.5 text-black/70" />
              </motion.button>
            </Link>

            <span className="text-[10px] text-white/40 font-mono">
              On-Device · Edge-Accelerated · Zero Video Retention
            </span>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}

export default Hero3DScene
