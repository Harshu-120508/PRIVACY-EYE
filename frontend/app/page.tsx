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
import { PrivacyGlowButton } from '@/components/core/privacy-glow-button'
import { Footer } from '@/components/layout/Footer'
import { Hero2DDisplay } from '@/components/landing/Hero2DDisplay'
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
    color: '#5EA7FF',
    description:
      'Detects micro-motion dynamics across eyes, nose tip, and mouth corners. Fuses 3D head yaw/pitch trajectory to invalidate 2D photo cutouts and silicone presentation attacks.',
    metrics: ['Sub-12ms Inference Latency', 'Continuous Pose Estimation', 'Laplacian Clarity Gating'],
    liveState: 'ACTIVE · 98.4% CONFIDENCE',
  },
  {
    id: 'silentface',
    title: 'Silent-Face Fourier PAD',
    subtitle: 'Dual-Scale 2D-FFT Presentation Attack Defense',
    icon: ShieldCheck,
    color: '#9B7CFF',
    description:
      'Transforms facial patches into frequency domains. Electronic screens (OLED, LCD, tablets) and printed paper emit distinct periodic moiré lattice spikes that are absent in natural human skin reflectance.',
    metrics: ['Dual-Scale Frequency Decomposition', 'Screen Moiré Suppression', 'Hard-Negative Replay Gated'],
    liveState: 'SAFE · 0.02 SPOOF PROBABILITY',
  },
  {
    id: 'forensics',
    title: 'FaceForensics++ Residuals',
    subtitle: 'High-Frequency DCT & ELA Seam Analysis',
    icon: Activity,
    color: '#38BDF8',
    description:
      'Inspects spatial compression artifacts and discrete cosine transform (DCT) coefficients. Identifies re-compression boundaries and blending seams typical of deepfake autoencoders and face-swapping algorithms.',
    metrics: ['Error Level Analysis (ELA)', 'Chroma Subsampling Checks', 'Zero-Seam Boundary Verification'],
    liveState: 'CLEAN · NO COMPOSITE RESIDUE',
  },
  {
    id: 'celebdf',
    title: 'Celeb-DF & FFHQ Realism',
    subtitle: 'Ocular Synthesis & Skin Texture Realism',
    icon: Sparkles,
    color: '#4ADE80',
    description:
      'Deep evaluation of corneal light reflection consistency, iris micro-jitter, and high-frequency biological skin pores matching the FFHQ organic baseline distribution.',
    metrics: ['Corneal Reflection Parallax', 'Biological Micro-Vascular Flux', 'FFHQ Organic Baseline'],
    liveState: 'VALIDATED · HIGH BIOLOGICAL REALISM',
  },
]

export default function LandingPage() {
  const router = useRouter()
  const [selectedFeature, setSelectedFeature] = useState<FeatureDetail | null>(null)
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [authMode, setAuthMode] = useState<'LOGIN' | 'REGISTER'>('LOGIN')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
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
        await authApi.register(authEmail, authPassword, authName)
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
    <div className="relative min-h-screen flex flex-col bg-canvas text-white selection:bg-brand-cyan/30 overflow-x-hidden">
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
            <a href="#hero" className="hover:text-white transition-colors">
              Authenticity Engine
            </a>
            <a href="#features" className="hover:text-white transition-colors">
              Forensic Engines
            </a>
            <a href="#architecture" className="hover:text-white transition-colors">
              Privacy Enclave
            </a>
          </nav>

          {/* Right Action Buttons with 3D tactile clicks */}
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.94 }}
              onClick={() => {
                setAuthMode('LOGIN')
                setAuthModalOpen(true)
              }}
              className="text-xs font-semibold px-4 py-2 rounded-full glass-surface hover:bg-white/10 text-white/80 transition-all border border-white/10 cursor-pointer"
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
              className="text-xs font-bold px-5 py-2 rounded-full bg-gradient-to-r from-brand-cyan via-brand-cyan to-brand-violet text-white shadow-glow-cyan border border-white/20 transition-all cursor-pointer"
            >
              Get Started
            </motion.button>
          </div>
        </motion.div>
      </header>

      {/* ── HERO 2D FORENSIC SUITE ── */}
      <section id="hero" className="relative pt-32 md:pt-40 pb-16 px-4 md:px-8 max-w-7xl mx-auto w-full flex flex-col items-center text-center">
        {/* Top Badge */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-surface border border-brand-cyan/30 mb-6 shadow-glow-cyan text-xs font-mono text-brand-cyan"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-cyan opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-cyan" />
          </span>
          <span>MULTI-SIGNAL BIOMETRICS · REAL-TIME AI FORENSICS</span>
        </motion.div>

        {/* Main Title */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tight leading-[1.04] max-w-5xl"
        >
          SEE THROUGH{' '}
          <span className="bg-gradient-to-r from-brand-cyan via-brand-cyan to-brand-violet bg-clip-text text-transparent">
            THE FAKE.
          </span>
        </motion.h1>

        {/* Subheading */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="mt-6 text-base md:text-xl text-white/70 max-w-2xl font-normal leading-relaxed"
        >
          AI-powered digital authenticity and deepfake protection. Multi-spectral biometric tracking
          and forensic analysis built for the AI era.
        </motion.p>

        {/* ── THE 2D BIOMETRIC DISPLAY ── */}
        <div className="w-full mt-6">
          <Hero2DDisplay />
        </div>
      </section>

      {/* ── MULTI-SIGNAL FORENSIC ENGINE MATRICES ── */}
      <section id="features" className="py-24 px-4 md:px-8 max-w-7xl mx-auto w-full space-y-12">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <span className="text-xs font-mono uppercase tracking-widest text-brand-cyan">
            Multi-Signal Forensic Defense
          </span>
          <h2 className="text-3xl md:text-5xl font-extrabold tracking-tight text-white">
            Forensic Engine Inspection
          </h2>
          <p className="text-sm text-white/60 leading-relaxed">
            Inspect real-time mathematical formulations, sensor telemetry, and active
            detection pipelines for each forensic neural engine.
          </p>
        </div>

        {/* Interactive 2D Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURES.map((feat) => {
            const Icon = feat.icon
            return (
              <motion.div
                key={feat.id}
                whileHover={{
                  y: -4,
                  transition: { duration: 0.2 },
                }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setSelectedFeature(feat)}
                className="relative rounded-3xl p-6 glass-floating border border-white/12 shadow-glass hover:border-brand-cyan/40 cursor-pointer overflow-hidden group text-left transition-colors"
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
                    <h3 className="text-lg font-bold text-white group-hover:text-brand-cyan transition-colors">
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
                    <span className="text-brand-cyan font-semibold flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                      Inspect <ArrowRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </section>

      {/* ── MODAL: FEATURE DETAIL INSPECTOR ── */}
      <AnimatePresence>
        {selectedFeature && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-2xl">
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: 10 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
              className="w-full max-w-2xl rounded-4xl glass-floating border border-white/20 p-8 md:p-10 space-y-6 shadow-glass-floating relative overflow-hidden text-left"
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

      {/* ── MODAL: FAST AUTHENTICATION DIALOG (Login & Sign Up) ── */}
      <AnimatePresence>
        {authModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-2xl">
            <motion.div
              initial={{ opacity: 0, scale: 0.96, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.96, y: 10 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
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

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  type="submit"
                  disabled={authLoading}
                  className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-brand-cyan to-brand-violet text-white font-bold text-xs tracking-wider uppercase shadow-glow-cyan mt-2 flex items-center justify-center gap-2 cursor-pointer"
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
      <section id="architecture" className="py-20 px-4 md:px-8 max-w-7xl mx-auto w-full">
        <div className="rounded-4xl glass-card p-8 md:p-12 border border-white/12 flex flex-col md:flex-row items-center justify-between gap-10">
          <div className="text-left max-w-xl space-y-4">
            <GlassBadge status="brand" label="ZERO DATA RETENTION ARCHITECTURE" />
            <h2 className="text-3xl md:text-4xl font-bold text-white">
              Privacy First. Always On-Device.
            </h2>
            <p className="text-sm text-white/70 leading-relaxed">
              We never store camera streams or facial recordings without signed consent. Frame
              buffers are processed in volatile memory and discarded within milliseconds.
            </p>
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

          <div className="flex flex-col gap-4 w-full md:w-auto">
            <Link href="/dashboard/live-scan">
              <PrivacyGlowButton size="lg" fullWidth>
                Launch Live Viewfinder
              </PrivacyGlowButton>
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
