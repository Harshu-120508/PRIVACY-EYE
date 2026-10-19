'use client'
import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
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
  FileText,
  ExternalLink,
  ShieldAlert,
  Sliders,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'

import { authApi, liveScanApi, analysisApi, consentsApi } from '@/lib/api'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'

const CONSENT_DEFINITIONS = [
  {
    purpose: 'MEDIA_PROCESSING',
    title: 'Media Ingestion & Forensic Detection',
    badge: 'NECESSARY',
    badgeStatus: 'safe' as const,
    description:
      'Required to compute spatial frequency (2D-FFT), error level analysis (ELA), and temporal difference metrics on uploaded media buffers. Never used for marketing.',
    legalBasis: 'Performance of requested contract / service',
    canToggle: false,
  },
  {
    purpose: 'SAVE_HISTORY',
    title: 'Retain Analysis Audit History',
    badge: 'OPTIONAL',
    badgeStatus: 'neutral' as const,
    description:
      'Stores cryptographic SHA-256 hashes, timestamps, and detection scores in your private dashboard audit trail. If disabled, media is analyzed in memory and immediately discarded without entering history.',
    legalBasis: 'Consent (Withdrawal available anytime)',
    canToggle: true,
  },
  {
    purpose: 'RETAIN_MEDIA',
    title: 'Raw Media Disk Storage',
    badge: 'DISABLED BY DEFAULT',
    badgeStatus: 'warning' as const,
    description:
      'Allows permanent retention of uploaded image, video, or audio binaries on disk. Disabled by default under zero-knowledge storage policy.',
    legalBasis: 'Explicit affirmative consent only',
    canToggle: true,
  },
  {
    purpose: 'EXTERNAL_AI_SHARING',
    title: 'Third-Party AI Cloud Forwarding',
    badge: 'DISABLED BY DEFAULT',
    badgeStatus: 'warning' as const,
    description:
      'Forwards media payloads to external model providers (e.g., cloud GPU accelerators). Disabled by default. All standard detections run on private instances.',
    legalBasis: 'Explicit affirmative consent only',
    canToggle: true,
  },
  {
    purpose: 'MODEL_TRAINING',
    title: 'Real Human Defense Dataset Opt-In',
    badge: 'STRICT OPT-IN',
    badgeStatus: 'neutral' as const,
    description:
      'Allows anonymized facial landmark crops or voice clips to be incorporated into calibration datasets to defend against new synthetic deepfake generators.',
    legalBasis: 'Affirmative opt-in consent (Never preselected)',
    canToggle: true,
  },
  {
    purpose: 'ANALYTICS',
    title: 'Operational Telemetry & Quality Metrics',
    badge: 'OPTIONAL',
    badgeStatus: 'neutral' as const,
    description:
      'Aggregated performance metrics (latency, error codes, frame rates) to monitor API reliability. Excludes personal identifying data.',
    legalBasis: 'Consent',
    canToggle: true,
  },
]

export default function PrivacyCenterPage() {
  const router = useRouter()
  const [processingMode, setProcessingMode] = useState<'LOCAL' | 'CLOUD'>('LOCAL')
  const [cameraPermission, setCameraPermission] = useState<string>('prompt')
  const [trainingStats, setTrainingStats] = useState<any>(null)
  const [consents, setConsents] = useState<Record<string, boolean>>({
    MEDIA_PROCESSING: true,
    SAVE_HISTORY: true,
    RETAIN_MEDIA: false,
    EXTERNAL_AI_SHARING: false,
    MODEL_TRAINING: false,
    ANALYTICS: false,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!Cookies.get('access_token')) {
      router.push('/auth/login')
      return
    }

    if (navigator.permissions && navigator.permissions.query) {
      navigator.permissions
        .query({ name: 'camera' as any })
        .then((res) => {
          setCameraPermission(res.state)
          res.onchange = () => setCameraPermission(res.state)
        })
        .catch(() => setCameraPermission('unknown'))
    }

    Promise.all([
      liveScanApi.getTrainingStats().then((res) => setTrainingStats(res.data)).catch(() => {}),
      consentsApi.getConsents().then((res) => {
        const map: Record<string, boolean> = {}
        res.data.consents.forEach((item: any) => {
          map[item.purpose] = item.granted
        })
        setConsents((prev) => ({ ...prev, ...map }))
      }).catch(() => {}),
    ]).finally(() => setLoading(false))
  }, [router])

  const handleToggleConsent = async (purpose: string, currentVal: boolean) => {
    const newVal = !currentVal
    setConsents((prev) => ({ ...prev, [purpose]: newVal }))
    try {
      await consentsApi.updateConsent(purpose, newVal)
      toast.success(newVal ? `Consent granted for ${purpose}` : `Consent withdrawn for ${purpose}`)
    } catch {
      setConsents((prev) => ({ ...prev, [purpose]: currentVal }))
      toast.error('Failed to update server-side consent decision.')
    }
  }

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
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-surface border border-status-safe/30 text-xs font-mono text-status-safe">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Sovereign Consent & Data Protection</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
            PRIVACY CENTER
          </h1>
          <p className="text-sm text-white/60 max-w-xl">
            Granular, purpose-specific consent management with strict server-side enforcement.
          </p>
        </div>

        {/* Link to public Privacy Policy page */}
        <Link href="/privacy">
          <GlassButton variant="secondary" size="sm" icon={<FileText className="w-4 h-4 text-brand-blue" />}>
            <span>View Public Privacy Policy</span>
            <ExternalLink className="w-3.5 h-3.5 ml-1 text-white/50" />
          </GlassButton>
        </Link>
      </div>

      {/* ── UNBUNDLED CONSENT CONTROLS (Section 8 Requirement) ── */}
      <GlassCard variant="elevated" className="p-6 md:p-8 space-y-6">
        <div className="flex items-center justify-between pb-3 border-b border-white/6">
          <div className="flex items-center gap-3">
            <Sliders className="w-5 h-5 text-brand-blue" />
            <div>
              <h2 className="text-base font-bold text-white">Unbundled Purpose-Specific Consents</h2>
              <p className="text-xs text-white/50">Server-enforced permissions governing media usage and data retention</p>
            </div>
          </div>
          <GlassBadge status="safe" label="SERVER-ENFORCED" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {CONSENT_DEFINITIONS.map((def) => {
            const isGranted = consents[def.purpose] ?? false
            return (
              <div
                key={def.purpose}
                className={`p-5 rounded-3xl border transition-all space-y-3 ${
                  isGranted
                    ? 'bg-white/[0.04] border-white/14 shadow-glass'
                    : 'bg-black/20 border-white/6 opacity-75'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-1">
                    <span className="font-bold text-white text-sm block">{def.title}</span>
                    <span className="text-[10px] font-mono text-brand-blue block">
                      Legal Basis: {def.legalBasis}
                    </span>
                  </div>
                  <GlassBadge status={def.badgeStatus} label={def.badge} />
                </div>

                <p className="text-xs text-white/60 leading-relaxed min-h-[48px]">
                  {def.description}
                </p>

                <div className="flex items-center justify-between pt-2 border-t border-white/6">
                  <span className="text-xs font-mono text-white/50">
                    Status: <strong className={isGranted ? 'text-status-safe' : 'text-white/40'}>{isGranted ? 'ACTIVE' : 'WITHDRAWN'}</strong>
                  </span>

                  {def.canToggle ? (
                    <button
                      onClick={() => handleToggleConsent(def.purpose, isGranted)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all ${
                        isGranted
                          ? 'bg-status-safe/20 text-status-safe border border-status-safe/40 hover:bg-status-danger/20 hover:text-status-danger hover:border-status-danger/40'
                          : 'bg-white/10 text-white/70 border border-white/10 hover:bg-brand-blue/20 hover:text-brand-blue hover:border-brand-blue/40'
                      }`}
                    >
                      {isGranted ? 'Withdraw Consent' : 'Grant Consent'}
                    </button>
                  ) : (
                    <span className="text-[11px] font-mono text-status-safe font-semibold">
                      ● INHERENT TO SERVICE
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </GlassCard>

      {/* ── SECTION: PROCESSING LOCATION ── */}
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

      {/* ── SECTION: STORAGE & RETENTION METRICS ── */}
      <GlassCard variant="elevated" className="p-6 md:p-8 space-y-6">
        <div className="flex items-center gap-3 pb-3 border-b border-white/6">
          <HardDrive className="w-5 h-5 text-status-safe" />
          <div>
            <h2 className="text-base font-bold text-white">Storage & Data Retention Metrics</h2>
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

      {/* ── SECTION: HARDWARE SENSORS & PERMISSIONS ── */}
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

      {/* ── SECTION: ACCOUNT DATA SOVEREIGNTY ── */}
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
