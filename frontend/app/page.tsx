'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Camera,
  UploadCloud,
  ShieldCheck,
  Cpu,
  Layers,
  Activity,
  ArrowRight,
  Lock,
  Eye,
  CheckCircle2,
  Sparkles,
  Zap,
  X,
  User,
  Mail,
  ChevronRight,
} from 'lucide-react'
import { BrandLogo } from '@/components/layout/BrandLogo'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'
import { Footer } from '@/components/layout/Footer'
import { Hero3DScene } from '@/components/landing/Hero3DScene'
import Particles from '@/components/reactbits/Particles'
import GridScan from '@/components/reactbits/GridScan'
import SpotlightCard from '@/components/reactbits/SpotlightCard'
import DecryptedText from '@/components/reactbits/DecryptedText'
import { AgentWaveCanvas } from '@/components/motion/AgentWaveCanvas'
import { ScrollRevealText } from '@/components/motion/ScrollRevealText'
import { authApi, getErrorMessage } from '@/lib/api'
import toast from 'react-hot-toast'
import { useRouter } from 'next/navigation'

interface FeatureDetail {
  id: string
  title: string
  subtitle: string
  icon: React.ElementType
  color: string
  description: string
  metrics: string[]
  liveState: string
}

const FEATURES: FeatureDetail[] = [
  {
    id: 'yunet',
    title: 'YuNet Biometric Tracking',
    subtitle: '5-Point Landmark Continuous Alignment',
    icon: Camera,
    color: '#FFFFFF',
    description:
      'Detects micro-motion dynamics across eyes, nose tip, and mouth corners. Fuses 3D head yaw/pitch trajectory with biological blink rates to invalidate 2D photo cutouts and silicone presentation attacks.',
    metrics: ['Sub-12ms Inference Latency', 'Continuous Pose Estimation', 'Laplacian Clarity Gating'],
    liveState: 'PIPELINE ACTIVE · ON-DEVICE YUNET',
  },
  {
    id: 'silentface',
    title: 'Silent-Face Fourier PAD',
    subtitle: 'Dual-Scale 2D-FFT Presentation Attack Defense',
    icon: ShieldCheck,
    color: '#E4E4E7',
    description:
      'Transforms facial patches into frequency domains. Electronic screens (OLED, LCD, tablets) and printed paper emit distinct periodic moiré lattice spikes that are absent in natural human skin reflectance.',
    metrics: ['Dual-Scale Frequency Decomposition', 'Screen Moiré Suppression', 'Hard-Negative Replay Gated'],
    liveState: 'PIPELINE ACTIVE · 2D-FFT SPECTRA',
  },
  {
    id: 'forensics',
    title: 'FaceForensics++ Residuals',
    subtitle: 'High-Frequency DCT & ELA Seam Analysis',
    icon: Activity,
    color: '#D4D4D8',
    description:
      'Inspects spatial compression artifacts and discrete cosine transform (DCT) coefficients. Identifies re-compression boundaries and blending seams typical of deepfake autoencoders and face-swapping algorithms.',
    metrics: ['Error Level Analysis (ELA)', 'Chroma Subsampling Checks', 'Zero-Seam Boundary Verification'],
    liveState: 'PIPELINE ACTIVE · DCT / ELA RESIDUALS',
  },
  {
    id: 'celebdf',
    title: 'Spatial Texture & Boundary Analysis',
    subtitle: 'High-Frequency Gradient & Diffusion Artifact Detection',
    icon: Sparkles,
    color: '#FFFFFF',
    description:
      'Deep evaluation of high-frequency texture gradient variance, boundary blending discontinuities, and ocular synthesis symmetry against organic photographic reference distributions.',
    metrics: ['Laplacian Variance Gating', 'Boundary Chroma Continuity', 'Organic Gradient Consistency'],
    liveState: 'PIPELINE ACTIVE · TEXTURE GRADIENTS',
  },
]

export default function LandingPage() {
  const router = useRouter()
  const [selectedFeature, setSelectedFeature] = useState<FeatureDetail | null>(null)
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [authMode, setAuthMode] = useState<'LOGIN' | 'REGISTER'>('LOGIN')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authConfirmPassword, setAuthConfirmPassword] = useState('')
  const [authName, setAuthName] = useState('')
  const [authLoading, setAuthLoading] = useState(false)

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setAuthLoading(true)
    try {
      if (authMode === 'LOGIN') {
        await authApi.login(authEmail, authPassword)
        toast.success('Access granted.')
      } else {
        if (authConfirmPassword && authPassword !== authConfirmPassword) {
          toast.error('Passwords do not match.')
          setAuthLoading(false)
          return
        }
        await authApi.register(authEmail, authPassword, authConfirmPassword || authPassword, authName)
        await authApi.login(authEmail, authPassword)
        toast.success('Account created and verified!')
      }
      setAuthModalOpen(false)
      router.push('/dashboard')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setAuthLoading(false)
    }
  }


  return (
    <div className="relative min-h-screen flex flex-col bg-canvas text-white selection:bg-brand-blue/30 overflow-x-hidden">
      {/* ── TOP FLOATING GLASS NAVIGATION (Matching Reference Pill) ── */}
      <header className="fixed top-4 left-0 right-0 z-50 px-4 md:px-8 max-w-7xl mx-auto pointer-events-none">
        <motion.div
          initial={{ y: -30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="pointer-events-auto flex items-center justify-between px-6 py-3.5 rounded-full glass-floating border border-white/16 backdrop-blur-2xl shadow-glass-floating"
        >
          <BrandLogo href="/" size="sm" />

          {/* Centered navigation items */}
          <nav className="hidden md:flex items-center gap-6 text-xs font-semibold tracking-wide text-white/70">
            <a href="#hero-3d" className="hover:text-white transition-colors">
              Authenticity 3D
            </a>
            <a href="#features-3d" className="hover:text-white transition-colors">
              Forensic Engines
            </a>
            <a href="#architecture" className="hover:text-white transition-colors">
              Privacy Enclave
            </a>
          </nav>

          {/* Right Action Buttons with Liquid-Metal MotionSites finish */}
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.94 }}
              onClick={() => {
                setAuthMode('LOGIN')
                setAuthModalOpen(true)
              }}
              className="text-xs font-semibold px-4 py-2 rounded-full pill-liquid-metal text-white/90 cursor-pointer"
            >
              Sign In
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05, translateY: -1 }}
              whileTap={{ scale: 0.94 }}
              onClick={() => {
                setAuthMode('REGISTER')
                setAuthModalOpen(true)
              }}
              className="text-xs font-bold px-5 py-2 rounded-full btn-liquid-metal cursor-pointer"
            >
              Get Started
            </motion.button>
          </div>
        </motion.div>
      </header>

      {/* ── HERO 3D INTERACTIVE EXPERIENCE (Agent Wave + React Bits) ── */}
      <section id="hero-3d" className="relative pt-32 md:pt-40 pb-12 px-4 md:px-8 max-w-7xl mx-auto w-full flex flex-col items-center text-center">
        {/* Agent Wave Sinusoidal Backdrop + Particle Field */}
        <div
          className="fixed inset-x-0 top-0 h-[920px] pointer-events-none z-0"
          style={{
            maskImage: 'linear-gradient(to bottom, rgba(0,0,0,1) 55%, transparent 100%)',
            WebkitMaskImage: 'linear-gradient(to bottom, rgba(0,0,0,1) 55%, transparent 100%)',
          }}
        >
          <AgentWaveCanvas className="absolute inset-0" opacity={0.55} speed={0.013} amplitude={42} />
          <Particles
            particleCount={65}
            particleSpread={9}
            speed={0.11}
            particleColors={['#ffffff', '#d4d4d8', '#71717a']}
            moveParticlesOnHover={true}
            particleHoverFactor={0.5}
            alphaParticles={true}
            particleBaseSize={80}
            connections={true}
            connectionDistance={115}
            opacity={0.38}
          />
        </div>

        {/* Top Badge (Blur-Rise Entrance) */}
        <motion.div
          initial={{ opacity: 0, y: 16, filter: 'blur(8px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ duration: 0.85, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 inline-flex items-center gap-2 px-4 py-1.5 rounded-full pill-liquid-metal mb-6 text-xs font-mono text-white/90"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-white" />
          </span>
          <DecryptedText
            text="OPERATIONAL AUTHENTICITY INFRASTRUCTURE · MOVE CURSOR & SCROLL"
            animateOn="view"
            sequential
            speed={32}
            revealDirection="start"
          />
        </motion.div>

        {/* Main Title (Agent Wave Mixed Sans + Instrument Serif Italic Accent) */}
        <motion.h1
          initial={{ opacity: 0, y: 26, filter: 'blur(10px)' }}
          animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
          transition={{ duration: 1.05, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight leading-[1.04] max-w-5xl text-white"
        >
          SEE THROUGH{' '}
          <motion.em
            initial={{ opacity: 0.35, filter: 'blur(5px)' }}
            animate={{ opacity: 1, filter: 'blur(0px)' }}
            transition={{ duration: 1.15, delay: 0.52, ease: [0.16, 1, 0.3, 1] }}
            className="font-editorial-italic text-[#b4b4bc] text-[1.09em] not-italic font-normal"
            style={{ fontStyle: 'italic' }}
          >
            the fake.
          </motion.em>
        </motion.h1>

        {/* Subheading */}
        <motion.p
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.0, delay: 0.45, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 mt-6 text-base md:text-xl text-[#9a9a9a] max-w-2xl font-normal leading-relaxed"
        >
          AI-powered digital authenticity and deepfake protection. Multi-spectral biometric tracking
          and forensic analysis built for the AI era.
        </motion.p>

        {/* Hero CTAs (Liquid-Metal Solid + Frosted Ghost) */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 mt-8 flex flex-wrap items-center justify-center gap-3"
        >
          <button
            onClick={() => {
              setAuthMode('REGISTER')
              setAuthModalOpen(true)
            }}
            className="px-6 py-3 rounded-xl text-sm font-semibold btn-liquid-metal inline-flex items-center gap-2 cursor-pointer"
          >
            <span>Start Protection</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <Link
            href="/dashboard/live-scan"
            className="px-6 py-3 rounded-xl text-sm font-medium pill-liquid-metal text-white inline-flex items-center gap-2 backdrop-blur-xl"
          >
            <Camera className="w-4 h-4 text-white/80" />
            <span>Launch Live Scan</span>
          </Link>
        </motion.div>

        {/* ── THE 3D SCENE (With Floating Glass Cards, Curvilinear Ribbons, and Cursor Parallax) ── */}
        <div className="relative z-10 w-full mt-6">
          <Hero3DScene />
        </div>

        {/* Agent Wave Crisp 3-Metric Strip */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.85, ease: [0.16, 1, 0.3, 1] }}
          className="relative z-10 w-full max-w-4xl mt-6 pt-8 border-t border-white/10 grid grid-cols-1 sm:grid-cols-3 gap-6 text-left sm:text-center"
        >
          <div className="flex sm:flex-col items-center gap-3 sm:gap-1.5 px-4">
            <div className="flex items-center gap-2 text-white font-mono text-sm font-bold tabular-nums">
              <Zap className="w-4 h-4 text-white/80" />
              <span>&lt; 12ms Inference</span>
            </div>
            <p className="text-xs text-[#9a9a9a]">On-device YuNet 5-landmark biometric tracking</p>
          </div>

          <div className="flex sm:flex-col items-center gap-3 sm:gap-1.5 px-4 sm:border-x border-white/10">
            <div className="flex items-center gap-2 text-white font-mono text-sm font-bold tabular-nums">
              <Layers className="w-4 h-4 text-white/80" />
              <span>Dual-Scale 2D-FFT</span>
            </div>
            <p className="text-xs text-[#9a9a9a]">Real-time spectral moire &amp; replay defense</p>
          </div>

          <div className="flex sm:flex-col items-center gap-3 sm:gap-1.5 px-4">
            <div className="flex items-center gap-2 text-white font-mono text-sm font-bold tabular-nums">
              <ShieldCheck className="w-4 h-4 text-status-safe" />
              <span>0 B Retained</span>
            </div>
            <p className="text-xs text-[#9a9a9a]">Volatile RAM buffers purged in milliseconds</p>
          </div>
        </motion.div>
      </section>

      {/* ── 3D INTERACTIVE FEATURE MATRICES (Section 19 & 30) ── */}
      <section id="features-3d" className="py-24 px-4 md:px-8 max-w-7xl mx-auto w-full space-y-12">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <span className="text-xs font-mono uppercase tracking-widest text-brand-blue">
            Multi-Signal Forensic Defense
          </span>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight text-white">
            Click Any Engine for 3D Forensic Inspection
          </h2>
          <p className="text-sm text-white/60 leading-relaxed">
            Click on any forensic card below to open its real-time mathematical formulation,
            sensor telemetry, and active detection pipeline.
          </p>
        </div>

        {/* Interactive 3D Spotlight Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" style={{ perspective: '1000px' }}>
          {FEATURES.map((feat) => {
            const Icon = feat.icon
            return (
              <motion.div
                key={feat.id}
                whileHover={{
                  scale: 1.04,
                  rotateX: 6,
                  rotateY: -4,
                  translateZ: 25,
                  transition: { duration: 0.25 },
                }}
                whileTap={{ scale: 0.96 }}
                className="h-full"
                style={{ transformStyle: 'preserve-3d' }}
              >
                <SpotlightCard
                  onClick={() => setSelectedFeature(feat)}
                  spotlightColor={feat.color}
                  intensity={0.18}
                  spotlightSize={260}
                  borderGlow={0.75}
                  className="relative h-full !rounded-3xl !p-6 glass-floating border border-white/12 shadow-glass hover:border-white/40 cursor-pointer group text-left transition-colors"
                  style={{ backgroundColor: 'rgba(10, 10, 10, 0.72)' }}
                >
                  {/* Background ambient corner flare */}
                  <div
                    className="absolute -top-10 -right-10 w-32 h-32 rounded-full opacity-20 group-hover:opacity-40 transition-opacity blur-2xl pointer-events-none"
                    style={{ background: feat.color }}
                  />

                  <div className="relative z-10 space-y-4">
                    <div
                      className="w-12 h-12 rounded-2xl flex items-center justify-center border shadow-sm transition-transform duration-300 group-hover:scale-110"
                      style={{
                        background: `${feat.color}15`,
                        borderColor: `${feat.color}35`,
                        color: feat.color,
                      }}
                    >
                      <Icon className="w-6 h-6" />
                    </div>

                    <div>
                      <h3 className="text-lg font-bold text-white group-hover:text-white transition-colors">
                        {feat.title}
                      </h3>
                      <p className="text-xs text-white/50 mt-1 font-mono">{feat.subtitle}</p>
                    </div>

                    <p className="text-xs text-white/70 line-clamp-3 leading-relaxed">
                      {feat.description}
                    </p>

                    <div className="pt-2 flex items-center justify-between border-t border-white/6 text-xs">
                      <span className="font-mono text-[10px] text-status-safe font-bold">
                        {feat.liveState.split('·')[0]}
                      </span>
                      <span className="text-white font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                        Inspect <ArrowRight className="w-3.5 h-3.5" />
                      </span>
                    </div>
                  </div>
                </SpotlightCard>
              </motion.div>
            )
          })}
        </div>
      </section>

      {/* ── 3D MODAL: FEATURE DETAIL INSPECTOR ── */}
      <AnimatePresence>
        {selectedFeature && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-2xl">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, rotateX: 12 }}
              animate={{ opacity: 1, scale: 1, rotateX: 0 }}
              exit={{ opacity: 0, scale: 0.9, rotateX: 12 }}
              transition={{ type: 'spring', damping: 25, stiffness: 220 }}
              className="w-full max-w-2xl rounded-4xl glass-floating border border-white/20 p-8 md:p-10 space-y-6 shadow-glass-floating relative overflow-hidden text-left"
              style={{ perspective: '1200px' }}
            >
              {/* Top ambient color glow */}
              <div
                className="absolute top-0 right-0 w-72 h-72 rounded-full opacity-25 blur-3xl pointer-events-none"
                style={{ background: selectedFeature.color }}
              />

              <div className="flex items-center justify-between pb-4 border-b border-white/8 relative z-10">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-2xl flex items-center justify-center border"
                    style={{
                      background: `${selectedFeature.color}20`,
                      borderColor: `${selectedFeature.color}40`,
                      color: selectedFeature.color,
                    }}
                  >
                    <selectedFeature.icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">{selectedFeature.title}</h3>
                    <p className="text-xs text-white/50 font-mono">{selectedFeature.subtitle}</p>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedFeature(null)}
                  className="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center text-white/60 hover:text-white transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-4 relative z-10 text-sm leading-relaxed text-white/80 font-sans">
                <p>{selectedFeature.description}</p>

                <div className="space-y-2 pt-2">
                  <span className="text-xs uppercase font-mono text-white/50 tracking-wider block">
                    Telemetry & Algorithmic Parameters:
                  </span>
                  <div className="space-y-2">
                    {selectedFeature.metrics.map((metric, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-2xl bg-white/4 border border-white/8 flex items-center gap-2.5 text-xs font-mono text-white"
                      >
                        <CheckCircle2 className="w-4 h-4 text-status-safe flex-shrink-0" />
                        <span>{metric}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-3xl bg-white/3 border border-white/8 flex items-center justify-between">
                  <span className="text-xs font-mono text-white/50">Current Sensor Telemetry:</span>
                  <span className="text-xs font-mono font-bold text-status-safe">
                    {selectedFeature.liveState}
                  </span>
                </div>
              </div>

              <div className="pt-4 border-t border-white/8 flex items-center justify-end gap-3 relative z-10">
                <GlassButton variant="secondary" size="md" onClick={() => setSelectedFeature(null)}>
                  Close
                </GlassButton>
                <Link href="/dashboard/live-scan">
                  <GlassButton variant="primary" size="md" icon={<Camera className="w-4 h-4" />}>
                    Test on Live Camera
                  </GlassButton>
                </Link>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── 3D MODAL: FAST AUTHENTICATION DIALOG (Login & Sign Up) ── */}
      <AnimatePresence>
        {authModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-2xl">
            <motion.div
              initial={{ opacity: 0, scale: 0.92, rotateY: 15 }}
              animate={{ opacity: 1, scale: 1, rotateY: 0 }}
              exit={{ opacity: 0, scale: 0.92, rotateY: 15 }}
              transition={{ type: 'spring', damping: 25, stiffness: 220 }}
              className="w-full max-w-md rounded-4xl glass-floating border border-white/20 p-8 space-y-6 shadow-glass-floating relative text-left"
            >
              <div className="flex items-center justify-between pb-3 border-b border-white/8">
                <BrandLogo size="sm" />
                <button
                  onClick={() => setAuthModalOpen(false)}
                  className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-white/60 hover:text-white transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Mode Toggle Tabs */}
              <div className="flex p-1 rounded-2xl glass-surface border border-white/8">
                <button
                  onClick={() => setAuthMode('LOGIN')}
                  className={`flex-1 py-2 rounded-xl text-xs font-bold tracking-wide transition-all ${
                    authMode === 'LOGIN' ? 'bg-white/10 text-white shadow-sm' : 'text-white/50'
                  }`}
                >
                  Sign In
                </button>
                <button
                  onClick={() => setAuthMode('REGISTER')}
                  className={`flex-1 py-2 rounded-xl text-xs font-bold tracking-wide transition-all ${
                    authMode === 'REGISTER' ? 'bg-white/10 text-white shadow-sm' : 'text-white/50'
                  }`}
                >
                  Create Account
                </button>
              </div>

              <form onSubmit={handleAuthSubmit} className="space-y-4">
                {authMode === 'REGISTER' && (
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-white/70">Full Name</label>
                    <div className="relative">
                      <User className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                      <input
                        type="text"
                        placeholder="Security Analyst"
                        value={authName}
                        onChange={(e) => setAuthName(e.target.value)}
                        className="glass-input pl-11 text-xs"
                        required
                      />
                    </div>
                  </div>
                )}

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-white/70">Email Address</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                    <input
                      type="email"
                      placeholder="analyst@enterprise.com"
                      value={authEmail}
                      onChange={(e) => setAuthEmail(e.target.value)}
                      className="glass-input pl-11 text-xs"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-white/70">Password</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                    <input
                      type="password"
                      placeholder="••••••••••••"
                      value={authPassword}
                      onChange={(e) => setAuthPassword(e.target.value)}
                      className="glass-input pl-11 text-xs"
                      required
                    />
                  </div>
                </div>

                {authMode === 'REGISTER' && (
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-white/70">Confirm Password</label>
                    <div className="relative">
                      <Lock className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                      <input
                        type="password"
                        placeholder="••••••••••••"
                        value={authConfirmPassword}
                        onChange={(e) => setAuthConfirmPassword(e.target.value)}
                        className="glass-input pl-11 text-xs"
                        required
                      />
                    </div>
                  </div>
                )}


                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  type="submit"
                  disabled={authLoading}
                  className="w-full py-3.5 rounded-2xl bg-white text-black font-bold text-xs tracking-wider uppercase shadow-md hover:bg-neutral-200 mt-2 flex items-center justify-center gap-2 cursor-pointer transition-all"
                >
                  {authLoading ? 'Verifying...' : authMode === 'LOGIN' ? 'Sign In & Launch' : 'Create & Access'}
                  <ArrowRight className="w-4 h-4" />
                </motion.button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ── ZERO-RETENTION PRIVACY PROMISE ── */}
      <section id="architecture" className="py-20 px-4 md:px-8 max-w-7xl mx-auto w-full relative z-10">
        <div className="relative overflow-hidden rounded-4xl glass-card p-8 md:p-12 border border-white/12 flex flex-col md:flex-row items-center justify-between gap-10">
          {/* React Bits Forensic GridScan Background */}
          <div className="absolute inset-0 pointer-events-none opacity-35">
            <GridScan
              linesColor="#27272a"
              scanColor="#4ade80"
              cells={10}
              autoScan={true}
              scanDuration={2.8}
              scanDelay={1.6}
              glow={0.55}
              interactive={true}
            />
          </div>

          <div className="relative z-10 text-left max-w-xl space-y-5">
            <GlassBadge status="neutral" label="ZERO DATA RETENTION ARCHITECTURE" />
            <h2 className="text-3xl md:text-4xl font-bold text-white">
              Privacy First.{' '}
              <span className="font-editorial-italic text-[#b4b4bc] text-[1.08em]">
                Always On-Device.
              </span>
            </h2>
            <ScrollRevealText
              text="We never store camera streams or facial recordings without signed consent. Frame buffers are processed in volatile memory and discarded within milliseconds."
              highlightWords={['never', 'consent', 'volatile', 'milliseconds']}
              className="text-base md:text-lg font-medium leading-relaxed tracking-tight"
            />
            <div className="pt-2 flex items-center gap-6 text-xs text-white/80">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-status-safe" />
                <span>Encrypted in Transit</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-status-safe" />
                <span>On-Device Neural Engine</span>
              </div>
            </div>
          </div>

          <div className="relative z-10 flex flex-col gap-4 w-full md:w-auto">
            <Link href="/dashboard/live-scan">
              <GlassButton variant="primary" size="lg" className="w-full">
                Launch Live Viewfinder
              </GlassButton>
            </Link>
            <Link href="/dashboard/privacy">
              <GlassButton variant="secondary" size="lg" className="w-full">
                Review Privacy Center
              </GlassButton>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  )
}
