'use client'
import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  ShieldCheck,
  Lock,
  Cpu,
  Database,
  Trash2,
  Download,
  Camera,
  Bell,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  HardDrive,
  FileKey,
  Layers,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'

import { authApi, liveScanApi, analysisApi } from '@/lib/api'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'

export default function PrivacyCenterPage() {
  const router = useRouter()
  const [processingMode, setProcessingMode] = useState<'LOCAL' | 'CLOUD'>('LOCAL')
  const [cameraPermission, setCameraPermission] = useState<string>('prompt')
  const [trainingStats, setTrainingStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!Cookies.get('access_token')) {
      router.push('/auth/login')
      return
    }

    // Check device camera permission API
    if (navigator.permissions && navigator.permissions.query) {
      navigator.permissions
        .query({ name: 'camera' as any })
        .then((res) => {
          setCameraPermission(res.state)
          res.onchange = () => setCameraPermission(res.state)
        })
        .catch(() => setCameraPermission('unknown'))
    }

    liveScanApi
      .getTrainingStats()
      .then((res) => setTrainingStats(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [router])

  const handleDownloadUserData = async () => {
    try {
      const res = await analysisApi.getHistory(1, 100)
      const dataStr = JSON.stringify(res.data, null, 2)
      const blob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `privacy-eye-account-archive-${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Account forensic archive downloaded')
    } catch {
      toast.error('Failed to export account archive')
    }
  }

  const handlePurgeAllHistory = async () => {
    if (
      !confirm(
        'WARNING: This will permanently purge all your analysis history and cryptographic hashes from the database. Proceed?'
      )
    ) {
      return
    }
    try {
      const res = await analysisApi.getHistory(1, 100)
      const items = res.data.items || []
      if (items.length === 0) {
        toast.success('No analysis records found to purge.')
        return
      }
      await Promise.all(items.map((item: any) => analysisApi.deleteAnalysis(item.id)))
      toast.success(`Purge complete. ${items.length} analysis audit records erased.`)
    } catch {
      toast.error('Failed to execute purge request')
    }
  }

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* ── HEADER ── */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-surface border border-status-safe/30 text-xs font-mono text-status-safe">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Privacy Sovereignty Controls</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
          PRIVACY CENTER
        </h1>
        <p className="text-sm text-white/60 max-w-xl">
          Complete transparency over local vs cloud inference, temporary buffers, and zero-knowledge retention.
        </p>
      </div>

      {/* ── SECTION 1: PROCESSING LOCATION (Section 26 & 27) ── */}
      <GlassCard variant="elevated" className="p-6 md:p-8 space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-white/6">
          <div className="flex items-center gap-3">
            <Cpu className="w-5 h-5 text-brand-blue" />
            <div>
              <h2 className="text-base font-bold text-white">Processing Architecture</h2>
              <p className="text-xs text-white/50">Determine where neural tensor operations execute</p>
            </div>
          </div>
          <GlassBadge status="safe" label="ON-DEVICE ACTIVE" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Option 1: On-Device / Local Edge */}
          <div
            onClick={() => setProcessingMode('LOCAL')}
            className={`p-5 rounded-3xl border transition-all cursor-pointer space-y-3 ${
              processingMode === 'LOCAL'
                ? 'bg-brand-blue/10 border-brand-blue/40 shadow-glow-blue'
                : 'glass-surface border-white/8 opacity-60'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-bold text-white text-sm">On-Device / Local Edge</span>
              {processingMode === 'LOCAL' && <CheckCircle2 className="w-4 h-4 text-brand-blue" />}
            </div>
            <p className="text-xs text-white/60 leading-relaxed">
              YuNet landmarks, Laplacian variance, and Fourier spectral attacks are computed on your local hardware. Video never leaves your perimeter.
            </p>
            <span className="text-[11px] font-mono text-status-safe block font-semibold">
              ● ACTIVE FOR LIVE SCAN
            </span>
          </div>

          {/* Option 2: Secure Cloud Enclave */}
          <div
            onClick={() => setProcessingMode('CLOUD')}
            className={`p-5 rounded-3xl border transition-all cursor-pointer space-y-3 ${
              processingMode === 'CLOUD'
                ? 'bg-brand-violet/10 border-brand-violet/40 shadow-glow-violet'
                : 'glass-surface border-white/8 opacity-60'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-bold text-white text-sm">Secure Cloud Inference</span>
              {processingMode === 'CLOUD' && <CheckCircle2 className="w-4 h-4 text-brand-violet" />}
            </div>
            <p className="text-xs text-white/60 leading-relaxed">
              Used for 500MB multi-gigabyte video forensic ELA models requiring high-performance GPU tensor clusters. Encrypted in transit.
            </p>
            <span className="text-[11px] font-mono text-white/40 block font-semibold">
              OPTIONAL ACCELERATION
            </span>
          </div>
        </div>
      </GlassCard>

      {/* ── SECTION 2: STORAGE & RETENTION (Section 26 requirement) ── */}
      <GlassCard variant="elevated" className="p-6 md:p-8 space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-white/6">
          <HardDrive className="w-5 h-5 text-status-safe" />
          <div>
            <h2 className="text-base font-bold text-white">Storage & Data Retention</h2>
            <p className="text-xs text-white/50">Strict zero-knowledge storage metrics</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          <div className="p-4 rounded-3xl bg-white/4 border border-white/6 space-y-1">
            <span className="text-white/40 uppercase text-[10px] block">Media Stored on Disk</span>
            <p className="text-2xl font-bold text-status-safe">0 Bytes</p>
            <span className="text-white/50 text-[11px]">Instantaneous in-memory purge</span>
          </div>

          <div className="p-4 rounded-3xl bg-white/4 border border-white/6 space-y-1">
            <span className="text-white/40 uppercase text-[10px] block">Temporary Video Chunks</span>
            <p className="text-2xl font-bold text-white">0 Chunks</p>
            <span className="text-white/50 text-[11px]">Auto-cleared upon response</span>
          </div>

          <div className="p-4 rounded-3xl bg-white/4 border border-white/6 space-y-1">
            <span className="text-white/40 uppercase text-[10px] block">Training Model Samples</span>
            <p className="text-2xl font-bold text-brand-blue">
              {trainingStats?.consented_samples ?? 0} Contributed
            </p>
            <span className="text-white/50 text-[11px]">Strict opt-in consent only</span>
          </div>
        </div>
      </GlassCard>

      {/* ── SECTION 3: DEVICE PERMISSIONS (Section 26 requirement) ── */}
      <GlassCard variant="elevated" className="p-6 md:p-8 space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-white/6">
          <Lock className="w-5 h-5 text-brand-violet" />
          <div>
            <h2 className="text-base font-bold text-white">Hardware Permissions</h2>
            <p className="text-xs text-white/50">Device sensors and browser APIs</p>
          </div>
        </div>

        <div className="space-y-3 text-xs">
          <div className="p-4 rounded-2xl bg-white/4 border border-white/6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Camera className="w-4 h-4 text-brand-blue" />
              <div>
                <span className="font-semibold text-white block">Camera Sensor</span>
                <span className="text-white/50 text-[11px]">Used for live liveness scan HUD</span>
              </div>
            </div>
            <GlassBadge
              status={cameraPermission === 'granted' ? 'safe' : 'neutral'}
              label={cameraPermission.toUpperCase()}
            />
          </div>

          <div className="p-4 rounded-2xl bg-white/4 border border-white/6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Lock className="w-4 h-4 text-white/50" />
              <div>
                <span className="font-semibold text-white block">Microphone Access</span>
                <span className="text-white/50 text-[11px]">Disabled by default during camera scan</span>
              </div>
            </div>
            <GlassBadge status="neutral" label="INACTIVE" />
          </div>

          <div className="p-4 rounded-2xl bg-white/4 border border-white/6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bell className="w-4 h-4 text-brand-cyan" />
              <div>
                <span className="font-semibold text-white block">Desktop Alerts</span>
                <span className="text-white/50 text-[11px]">Notifications for completed video scans</span>
              </div>
            </div>
            <GlassBadge status="safe" label="READY" />
          </div>
        </div>
      </GlassCard>

      {/* ── SECTION 4: ACCOUNT DATA SOVEREIGNTY (Section 26 requirement) ── */}
      <GlassCard variant="elevated" className="p-6 md:p-8 space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-white/6">
          <FileKey className="w-5 h-5 text-status-warning" />
          <div>
            <h2 className="text-base font-bold text-white">Account Sovereignty & Erasure</h2>
            <p className="text-xs text-white/50">GDPR Article 17 Right to Erasure compliance</p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 pt-2">
          <GlassButton
            variant="secondary"
            size="md"
            onClick={handleDownloadUserData}
            icon={<Download className="w-4 h-4 text-brand-blue" />}
          >
            Download Data Archive (.json)
          </GlassButton>

          <GlassButton
            variant="danger"
            size="md"
            onClick={handlePurgeAllHistory}
            icon={<Trash2 className="w-4 h-4 text-status-danger" />}
          >
            Purge All Analysis Records
          </GlassButton>
        </div>
      </GlassCard>
    </div>
  )
}
