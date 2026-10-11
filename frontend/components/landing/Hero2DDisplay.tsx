'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  Camera,
  UploadCloud,
  ShieldCheck,
  Activity,
  CheckCircle2,
  ArrowRight,
  Cpu,
  Lock,
  Layers,
  Sparkles,
  Zap,
} from 'lucide-react'
import { PrivacyGlowButton } from '@/components/core/privacy-glow-button'

export const Hero2DDisplay: React.FC = () => {
  const [activeCallout, setActiveCallout] = useState<string | null>(null)

  return (
    <div className="relative w-full max-w-6xl mx-auto flex flex-col lg:flex-row items-center gap-10 lg:gap-14 py-4 select-none">
      {/* ── LEFT / MAIN: FACIAL BIOMETRIC FORENSIC HUD ── */}
      <div className="relative w-full lg:w-[60%] flex flex-col items-center">
        {/* HUD Frame Container */}
        <div className="relative w-full max-w-lg aspect-[4/3] rounded-3xl bg-[#050505] border border-white/[0.08] p-4 sm:p-6 overflow-hidden shadow-2xl">
          {/* Subtle Ambient Radial Glow */}
          <div
            className="absolute -top-16 -left-16 w-64 h-64 rounded-full pointer-events-none opacity-40"
            style={{
              background: 'radial-gradient(circle, rgba(19, 210, 232, 0.2) 0%, transparent 70%)',
            }}
          />
          <div
            className="absolute -bottom-16 -right-16 w-64 h-64 rounded-full pointer-events-none opacity-30"
            style={{
              background: 'radial-gradient(circle, rgba(192, 16, 237, 0.2) 0%, transparent 70%)',
            }}
          />

          {/* Micro Grid Background */}
          <div
            className="absolute inset-0 opacity-15 pointer-events-none"
            style={{
              backgroundImage:
                'linear-gradient(to right, rgba(255, 255, 255, 0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(255, 255, 255, 0.08) 1px, transparent 1px)',
              backgroundSize: '28px 28px',
            }}
          />

          {/* Top Status Bar */}
          <div className="relative z-10 flex items-center justify-between pb-3 border-b border-white/[0.06] text-[11px] font-mono">
            <div className="flex items-center gap-2 text-brand-cyan">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-cyan opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-cyan" />
              </span>
              <span className="font-semibold tracking-wider">NEURAL VIEWPORT · 60 FPS</span>
            </div>
            <div className="flex items-center gap-2 text-white/50">
              <span className="text-white/40">RESOLUTION:</span>
              <span className="text-white/80 font-bold">1080P PRO</span>
            </div>
          </div>

          {/* Biometric Face Viewport Area */}
          <div className="relative w-full h-[calc(100%-36px)] mt-2 rounded-2xl bg-[#000000] border border-white/[0.04] flex items-center justify-center overflow-hidden">
            {/* SVG Biometric Face Silhouette & Mesh Landmarks */}
            <svg
              viewBox="0 0 320 280"
              className="w-full h-full max-w-[280px] max-h-[250px] text-white/30"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-label="Facial Biometric Analysis Mesh"
            >
              <defs>
                <linearGradient id="cyberMeshGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#13D2E8" stopOpacity="0.8" />
                  <stop offset="50%" stopColor="#FFFFFF" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#C010ED" stopOpacity="0.8" />
                </linearGradient>
                <linearGradient id="scanlineGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#13D2E8" stopOpacity="0" />
                  <stop offset="50%" stopColor="#13D2E8" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#13D2E8" stopOpacity="0" />
                </linearGradient>
              </defs>

              {/* Head Contour Path */}
              <path
                d="M160 30 C110 30 75 75 75 135 C75 195 105 240 160 255 C215 240 245 195 245 135 C245 75 210 30 160 30 Z"
                stroke="rgba(255, 255, 255, 0.18)"
                strokeWidth="1.5"
                strokeDasharray="4 3"
              />

              {/* Inner Facial Architecture Lines */}
              <ellipse cx="160" cy="140" rx="65" ry="85" stroke="rgba(255, 255, 255, 0.12)" strokeWidth="1" />

              {/* Eye Orbit Zones */}
              <ellipse cx="125" cy="118" rx="20" ry="12" stroke="#13D2E8" strokeWidth="1.5" strokeOpacity="0.7" />
              <ellipse cx="195" cy="118" rx="20" ry="12" stroke="#13D2E8" strokeWidth="1.5" strokeOpacity="0.7" />

              {/* Pupils / Irises */}
              <circle cx="125" cy="118" r="4.5" fill="#13D2E8" />
              <circle cx="195" cy="118" r="4.5" fill="#13D2E8" />
              <circle cx="125" cy="118" r="8" stroke="#13D2E8" strokeWidth="0.8" strokeDasharray="2 2" />
              <circle cx="195" cy="118" r="8" stroke="#13D2E8" strokeWidth="0.8" strokeDasharray="2 2" />

              {/* Eyebrows */}
              <path d="M108 102 C118 97 132 98 142 104" stroke="rgba(255, 255, 255, 0.35)" strokeWidth="1.5" strokeLinecap="round" />
              <path d="M178 104 C188 98 202 97 212 102" stroke="rgba(255, 255, 255, 0.35)" strokeWidth="1.5" strokeLinecap="round" />

              {/* Nose Bridge and Tip */}
              <path d="M160 110 L158 152 L150 160 H170 L162 152 Z" stroke="rgba(255, 255, 255, 0.25)" strokeWidth="1.2" />
              <circle cx="160" cy="158" r="3" fill="#13D2E8" fillOpacity="0.8" />

              {/* Mouth & Lips */}
              <path d="M136 195 C148 190 172 190 184 195 C172 205 148 205 136 195 Z" stroke="rgba(255, 255, 255, 0.3)" strokeWidth="1.2" />
              <path d="M132 195 H188" stroke="#13D2E8" strokeWidth="1" strokeOpacity="0.6" />

              {/* Geometric Landmark Vector Connections */}
              <line x1="125" y1="118" x2="160" y2="158" stroke="url(#cyberMeshGrad)" strokeWidth="0.8" strokeOpacity="0.6" />
              <line x1="195" y1="118" x2="160" y2="158" stroke="url(#cyberMeshGrad)" strokeWidth="0.8" strokeOpacity="0.6" />
              <line x1="160" y1="158" x2="136" y2="195" stroke="url(#cyberMeshGrad)" strokeWidth="0.8" strokeOpacity="0.6" />
              <line x1="160" y1="158" x2="184" y2="195" stroke="url(#cyberMeshGrad)" strokeWidth="0.8" strokeOpacity="0.6" />
              <line x1="125" y1="118" x2="195" y2="118" stroke="rgba(255, 255, 255, 0.15)" strokeWidth="0.8" strokeDasharray="3 3" />

              {/* Cheek / Texture Calibration Nodes */}
              <circle cx="112" cy="155" r="2.5" fill="#C010ED" />
              <circle cx="208" cy="155" r="2.5" fill="#C010ED" />
              <line x1="125" y1="118" x2="112" y2="155" stroke="rgba(192, 16, 237, 0.3)" strokeWidth="0.8" />
              <line x1="195" y1="118" x2="208" y2="155" stroke="rgba(192, 16, 237, 0.3)" strokeWidth="0.8" />
              <line x1="112" y1="155" x2="136" y2="195" stroke="rgba(192, 16, 237, 0.3)" strokeWidth="0.8" />
              <line x1="208" y1="155" x2="184" y2="195" stroke="rgba(192, 16, 237, 0.3)" strokeWidth="0.8" />

              {/* Viewport Corner Reticles */}
              <path d="M30 40 H45 M30 40 V55" stroke="#13D2E8" strokeWidth="2" strokeLinecap="round" />
              <path d="M290 40 H275 M290 40 V55" stroke="#13D2E8" strokeWidth="2" strokeLinecap="round" />
              <path d="M30 240 H45 M30 240 V225" stroke="#13D2E8" strokeWidth="2" strokeLinecap="round" />
              <path d="M290 240 H275 M290 240 V225" stroke="#13D2E8" strokeWidth="2" strokeLinecap="round" />
            </svg>

            {/* Scanning Line Animation (Lightweight 2D CSS) */}
            <div
              className="absolute inset-x-4 h-[2px] bg-gradient-to-r from-transparent via-[#13D2E8] to-transparent pointer-events-none animate-scan-vertical opacity-80 shadow-[0_0_12px_#13D2E8]"
            />

            {/* ── 2D HUD CALLOUTS (Directly Inspired by Nuvé Design Reference) ── */}
            {/* Callout 1: Top Left - YuNet Tracking */}
            <div
              className="absolute left-3 top-3 sm:left-4 sm:top-4 bg-[#080808]/90 border border-[#13D2E8]/40 rounded-xl px-2.5 py-1.5 shadow-lg backdrop-blur-md cursor-pointer transition-transform hover:scale-105"
              onMouseEnter={() => setActiveCallout('yunet')}
              onMouseLeave={() => setActiveCallout(null)}
            >
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#13D2E8]" />
                <span className="text-[10px] font-mono font-bold text-white tracking-wide">
                  YuNet 5-Point: 98.4%
                </span>
              </div>
              <div className="text-[9px] font-mono text-[#13D2E8]">Micro-Vector Stable</div>
            </div>

            {/* Callout 2: Top Right - Silent-Face PAD */}
            <div
              className="absolute right-3 top-3 sm:right-4 sm:top-4 bg-[#080808]/90 border border-[#C010ED]/40 rounded-xl px-2.5 py-1.5 shadow-lg backdrop-blur-md cursor-pointer transition-transform hover:scale-105"
              onMouseEnter={() => setActiveCallout('pad')}
              onMouseLeave={() => setActiveCallout(null)}
            >
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#C010ED]" />
                <span className="text-[10px] font-mono font-bold text-white tracking-wide">
                  Fourier PAD: Safe
                </span>
              </div>
              <div className="text-[9px] font-mono text-[#C010ED]">0.02 Spoof Index</div>
            </div>

            {/* Callout 3: Bottom Left - FaceForensics++ Seams */}
            <div
              className="absolute left-3 bottom-3 sm:left-4 sm:bottom-4 bg-[#080808]/90 border border-white/20 rounded-xl px-2.5 py-1.5 shadow-lg backdrop-blur-md cursor-pointer transition-transform hover:scale-105"
              onMouseEnter={() => setActiveCallout('forensics')}
              onMouseLeave={() => setActiveCallout(null)}
            >
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#13D2E8]" />
                <span className="text-[10px] font-mono font-bold text-white tracking-wide">
                  DCT Residuals: Clean
                </span>
              </div>
              <div className="text-[9px] font-mono text-white/50">Zero Blending Seams</div>
            </div>

            {/* Callout 4: Bottom Right - FFHQ Texture */}
            <div
              className="absolute right-3 bottom-3 sm:right-4 sm:bottom-4 bg-[#080808]/90 border border-white/20 rounded-xl px-2.5 py-1.5 shadow-lg backdrop-blur-md cursor-pointer transition-transform hover:scale-105"
              onMouseEnter={() => setActiveCallout('texture')}
              onMouseLeave={() => setActiveCallout(null)}
            >
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#13D2E8]" />
                <span className="text-[10px] font-mono font-bold text-white tracking-wide">
                  Biological Texture
                </span>
              </div>
              <div className="text-[9px] font-mono text-white/50">Organic Reflectance</div>
            </div>
          </div>
        </div>

        {/* Central HUD Caption Pill */}
        <div className="mt-3 inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#080808] border border-white/[0.08] text-[11px] font-mono text-white/60">
          <Lock className="w-3 h-3 text-brand-cyan" />
          <span>Real-time on-device inference · Zero remote frame transmission</span>
        </div>
      </div>

      {/* ── RIGHT: KEY METRIC STATS & ACTION BUTTONS (Matching Reference Clean Layout) ── */}
      <div className="w-full lg:w-[40%] flex flex-col justify-center space-y-6 text-left">
        {/* Metric Cards Stack (Minimalist 2D Counters) */}
        <div className="space-y-3.5">
          {/* Stat 1 */}
          <div className="p-4 rounded-2xl bg-[#050505] border border-white/[0.08] hover:border-brand-cyan/30 transition-colors flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-2xl sm:text-3xl font-extrabold font-mono tracking-tight text-white">
                99.2%
              </span>
              <p className="text-xs text-white/60">Forensic Detection Accuracy</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-brand-cyan/10 border border-brand-cyan/25 flex items-center justify-center text-brand-cyan">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </div>

          {/* Stat 2 */}
          <div className="p-4 rounded-2xl bg-[#050505] border border-white/[0.08] hover:border-brand-violet/30 transition-colors flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-2xl sm:text-3xl font-extrabold font-mono tracking-tight text-brand-cyan">
                &lt; 12ms
              </span>
              <p className="text-xs text-white/60">Ultra-Low Latency Inference</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-brand-violet/10 border border-brand-violet/25 flex items-center justify-center text-brand-violet">
              <Zap className="w-5 h-5" />
            </div>
          </div>

          {/* Stat 3 */}
          <div className="p-4 rounded-2xl bg-[#050505] border border-white/[0.08] hover:border-white/20 transition-colors flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-2xl sm:text-3xl font-extrabold font-mono tracking-tight text-white">
                0-Byte
              </span>
              <p className="text-xs text-white/60">Strict Zero-Retention Enclave</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/10 flex items-center justify-center text-white/80">
              <Lock className="w-5 h-5" />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <Link href="/dashboard/live-scan" className="flex-1">
            <PrivacyGlowButton size="md" fullWidth icon={<Camera className="w-4 h-4" />}>
              Launch Live Scan
            </PrivacyGlowButton>
          </Link>
          <Link href="/dashboard/analysis" className="flex-1">
            <button className="w-full py-3 px-5 rounded-xl bg-[#080808] hover:bg-white/[0.06] border border-white/[0.12] text-xs sm:text-sm font-semibold text-white/90 flex items-center justify-center gap-2 transition-all hover:border-white/25 active:scale-[0.98]">
              <UploadCloud className="w-4 h-4 text-brand-cyan" />
              <span>Upload Media</span>
            </button>
          </Link>
        </div>

        <div className="flex items-center gap-4 text-[11px] font-mono text-white/50">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-brand-cyan" />
            No plugins required
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-brand-cyan" />
            All browsers supported
          </span>
        </div>
      </div>
    </div>
  )
}

export default Hero2DDisplay
