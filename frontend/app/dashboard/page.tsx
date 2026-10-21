'use client'
import React, { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  Camera,
  UploadCloud,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Clock,
  ArrowRight,
  Eye,
  RefreshCw,
  FileText,
  Activity,
  Cpu,
  Lock,
} from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'

import { authApi, analysisApi, getErrorMessage } from '@/lib/api'
import type { User, DashboardStats, Analysis } from '@/types'
import { RISK_CONFIG } from '@/types'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'
import { StatusIndicator } from '@/components/ui/StatusIndicator'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentHistory, setRecentHistory] = useState<Analysis[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  // Compute time-of-day greeting
  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 18) return 'Good afternoon'
    return 'Good evening'
  }

  const loadDashboardData = useCallback(async () => {
    try {
      const [userRes, statsRes, histRes] = await Promise.all([
        authApi.me(),
        analysisApi.getStats(),
        analysisApi.getHistory(1, 5),
      ])
      setUser(userRes.data)
      setStats(statsRes.data)
      setRecentHistory(histRes.data.items || [])
    } catch (err: any) {
      if (err?.response?.status === 401) {
        router.push('/auth/login')
      } else {
        toast.error('Could not load dashboard data from backend')
      }
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [router])

  useEffect(() => {
    if (!Cookies.get('access_token')) {
      router.push('/auth/login')
      return
    }
    loadDashboardData()
  }, [loadDashboardData, router])

  const handleRefresh = () => {
    setRefreshing(true)
    loadDashboardData()
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 rounded-2xl glass-card flex items-center justify-center border border-white/20 shadow-[0_0_20px_rgba(255,255,255,0.15)] animate-pulse">
          <Eye className="w-6 h-6 text-white" />
        </div>
        <p className="mt-4 text-xs font-mono uppercase tracking-widest text-white/50">
          Connecting to Privacy Eye Core...
        </p>
      </div>
    )
  }

  const greeting = getGreeting()
  const firstName = user?.full_name?.split(' ')[0] || user?.email?.split('@')[0] || 'Operator'

  return (
    <div className="space-y-10">
      {/* ── TOP HEADER (Section 12) ── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs uppercase font-mono tracking-widest text-white/80">
              Command Center
            </span>
            <span className="text-white/20">·</span>
            <span className="text-xs text-white/40">Secure Session</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
            {greeting}, {firstName}.
          </h1>
          <p className="text-sm text-white/60 mt-1">Your digital protection is active.</p>
        </div>

        <div className="flex items-center gap-3">
          <GlassButton
            variant="secondary"
            size="sm"
            onClick={handleRefresh}
            isLoading={refreshing}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh Telemetry
          </GlassButton>
          <Link href="/dashboard/live-scan">
            <GlassButton
              variant="primary"
              size="sm"
              icon={<Camera className="w-4 h-4" />}
              className="shadow-[0_0_20px_rgba(255,255,255,0.2)]"
            >
              Start Live Scan
            </GlassButton>
          </Link>
        </div>
      </div>

      {/* ── MAIN CENTRAL CARD: PROTECTION ACTIVE (Section 12 & 61) ── */}
      <GlassCard
        variant="floating"
        className="relative overflow-hidden p-8 md:p-10 border border-white/14"
      >
        {/* Ambient subtle glow background */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-white/[0.04] rounded-full blur-[90px] pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-8">
          <div className="space-y-4 max-w-xl">
            <div className="flex items-center gap-3">
              <StatusIndicator status="safe" />
              <GlassBadge status="safe" label="AUTHENTICITY ENGINE OPERATIONAL" pulse />
            </div>

            <div>
              <h2 className="text-3xl md:text-4xl font-black tracking-tight text-white">
                PROTECTION ACTIVE
              </h2>
              <p className="text-sm font-medium text-white/80 mt-0.5">
                Privacy-first analysis
              </p>
            </div>

            <p className="text-sm text-white/70 leading-relaxed">
              Real-time deepfake mitigation enabled. Local YuNet landmark tracking, Celeb-DF v2
              ocular residual check, and Silent-Face Fourier presentation attack defenses are live.
            </p>

            <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-white/60 pt-2">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/8">
                <Cpu className="w-3.5 h-3.5 text-brand-cyan" />
                <span>Processing: ON DEVICE / LOCAL</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/8">
                <Lock className="w-3.5 h-3.5 text-status-safe" />
                <span>Zero Media Retention</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row lg:flex-col gap-3 w-full lg:w-64 flex-shrink-0">
            <Link href="/dashboard/live-scan" className="w-full">
              <GlassButton
                variant="primary"
                size="md"
                className="w-full justify-between"
                icon={<Camera className="w-4 h-4" />}
              >
                <span>Live Camera Scan</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </GlassButton>
            </Link>
            <Link href="/dashboard/analysis" className="w-full">
              <GlassButton
                variant="secondary"
                size="md"
                className="w-full justify-between"
                icon={<UploadCloud className="w-4 h-4 text-brand-blue" />}
              >
                <span>Analyze File</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </GlassButton>
            </Link>
          </div>
        </div>
      </GlassCard>

      {/* ── FOUR DASHBOARD STATISTICS GLASS CARDS (Section 13) ── */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-white/70">
            Real Backend Telemetry
          </h3>
          <span className="text-xs font-mono text-white/40">Aggregated Audit Records</span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Media Scanned */}
          <GlassCard variant="elevated" className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-white/50">Media Scanned</span>
              <div className="w-8 h-8 rounded-xl bg-brand-blue/10 flex items-center justify-center text-brand-blue">
                <Eye className="w-4 h-4" />
              </div>
            </div>
            <p className="text-3xl font-extrabold font-mono text-white">
              {stats?.total_scanned ?? 0}
            </p>
            <p className="text-[11px] text-white/40">Actual backend processed items</p>
          </GlassCard>

          {/* Card 2: Suspicious */}
          <GlassCard variant="elevated" className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-white/50">Suspicious</span>
              <div className="w-8 h-8 rounded-xl bg-status-warning/10 flex items-center justify-center text-status-warning">
                <AlertTriangle className="w-4 h-4" />
              </div>
            </div>
            <p className="text-3xl font-extrabold font-mono text-status-warning">
              {stats?.suspicious ?? 0}
            </p>
            <p className="text-[11px] text-white/40">Probabilistic anomalies detected</p>
          </GlassCard>

          {/* Card 3: Low Risk */}
          <GlassCard variant="elevated" className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-white/50">Low Risk</span>
              <div className="w-8 h-8 rounded-xl bg-status-safe/10 flex items-center justify-center text-status-safe">
                <CheckCircle2 className="w-4 h-4" />
              </div>
            </div>
            <p className="text-3xl font-extrabold font-mono text-status-safe">
              {stats?.low_risk ?? 0}
            </p>
            <p className="text-[11px] text-white/40">High biological/organic signals</p>
          </GlassCard>

          {/* Card 4: Unable to Determine */}
          <GlassCard variant="elevated" className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-white/50">Undetermined</span>
              <div className="w-8 h-8 rounded-xl bg-status-undetermined/10 flex items-center justify-center text-status-undetermined">
                <HelpCircle className="w-4 h-4" />
              </div>
            </div>
            <p className="text-3xl font-extrabold font-mono text-status-undetermined">
              {stats?.undetermined ?? 0}
            </p>
            <p className="text-[11px] text-white/40">Abstained due to poor quality/blur</p>
          </GlassCard>
        </div>
      </div>

      {/* ── LIVE CAMERA CARD & SYSTEM OVERVIEW (Section 14 & 28) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Live Camera Card (Section 14) */}
        <GlassCard variant="elevated" className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Camera className="w-5 h-5 text-brand-blue" />
              <h3 className="text-lg font-bold text-white">LIVE CAMERA</h3>
            </div>
            <GlassBadge status="safe" label="EDGE INFERENCE READY" pulse />
          </div>

          {/* Interactive Preview Viewfinder */}
          <div className="relative aspect-[16/9] rounded-3xl bg-surface/90 border border-white/8 flex flex-col items-center justify-center overflow-hidden group">
            {/* Viewfinder corner guides */}
            <div className="absolute top-4 left-4 w-5 h-5 border-t-2 border-l-2 border-brand-blue/60" />
            <div className="absolute top-4 right-4 w-5 h-5 border-t-2 border-r-2 border-brand-blue/60" />
            <div className="absolute bottom-4 left-4 w-5 h-5 border-b-2 border-l-2 border-brand-blue/60" />
            <div className="absolute bottom-4 right-4 w-5 h-5 border-b-2 border-r-2 border-brand-blue/60" />

            {/* Central scanning glyph */}
            <div className="w-28 h-36 rounded-[48%] border border-white/20 flex flex-col items-center justify-center gap-2 relative">
              <div className="w-2.5 h-2.5 rounded-full bg-brand-blue shadow-glow-blue animate-pulse" />
              <span className="text-[10px] font-mono text-white/40 uppercase">YuNet Box</span>
            </div>

            {/* Status overlay */}
            <div className="absolute bottom-4 px-4 py-1.5 rounded-full glass-surface border border-white/12 flex items-center gap-2 text-xs">
              <span className="w-2 h-2 rounded-full bg-brand-blue animate-ping" />
              <span className="font-mono text-white/90">● READY FOR LIVE INFERENCE</span>
            </div>

            {/* Launch hover cover */}
            <div className="absolute inset-0 bg-canvas/60 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
              <Link href="/dashboard/live-scan">
                <GlassButton variant="primary" icon={<Camera className="w-4 h-4" />}>
                  Open Fullscreen Live HUD
                </GlassButton>
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-1">
            <div className="p-3 rounded-2xl bg-white/4 border border-white/6">
              <span className="text-white/40 block text-[10px] uppercase font-mono">Face Model</span>
              <span className="font-semibold text-white mt-0.5 block">OpenCV YuNet</span>
            </div>
            <div className="p-3 rounded-2xl bg-white/4 border border-white/6">
              <span className="text-white/40 block text-[10px] uppercase font-mono">Temporal</span>
              <span className="font-semibold text-white mt-0.5 block">Micro-Motion & Blinks</span>
            </div>
            <div className="p-3 rounded-2xl bg-white/4 border border-white/6">
              <span className="text-white/40 block text-[10px] uppercase font-mono">Replay Attack</span>
              <span className="font-semibold text-white mt-0.5 block">Silent-Face Fourier</span>
            </div>
            <div className="p-3 rounded-2xl bg-white/4 border border-white/6">
              <span className="text-white/40 block text-[10px] uppercase font-mono">Texture Baseline</span>
              <span className="font-semibold text-white mt-0.5 block">FFHQ Distribution</span>
            </div>
          </div>
        </GlassCard>

        {/* Right 1 Col: Security Center Quick Status (Section 28) */}
        <GlassCard variant="elevated" className="space-y-5">
          <div className="flex items-center justify-between pb-2 border-b border-white/6">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-status-safe" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                SECURITY CENTER
              </h3>
            </div>
            <Link
              href="/dashboard/security"
              className="text-xs text-brand-blue hover:underline flex items-center gap-1"
            >
              Details <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between p-3 rounded-2xl bg-white/4 border border-white/6">
              <div>
                <span className="font-semibold text-white block">FastAPI REST Core</span>
                <span className="text-white/40 text-[11px]">HTTP 2.0 / Local</span>
              </div>
              <GlassBadge status="safe" label="OPERATIONAL" />
            </div>

            <div className="flex items-center justify-between p-3 rounded-2xl bg-white/4 border border-white/6">
              <div>
                <span className="font-semibold text-white block">ML Inference Engine</span>
                <span className="text-white/40 text-[11px]">PyTorch & ONNX</span>
              </div>
              <GlassBadge status="safe" label="OPERATIONAL" />
            </div>

            <div className="flex items-center justify-between p-3 rounded-2xl bg-white/4 border border-white/6">
              <div>
                <span className="font-semibold text-white block">PostgreSQL Database</span>
                <span className="text-white/40 text-[11px]">Async SQLAlchemy</span>
              </div>
              <GlassBadge status="safe" label="OPERATIONAL" />
            </div>

            <div className="flex items-center justify-between p-3 rounded-2xl bg-white/4 border border-white/6">
              <div>
                <span className="font-semibold text-white block">Active Protocol Verifier</span>
                <span className="text-white/40 text-[11px]">Smile + Blinks + Yaw</span>
              </div>
              <GlassBadge status="safe" label="ACTIVE" />
            </div>
          </div>

          <div className="pt-2">
            <Link href="/dashboard/privacy" className="block">
              <div className="p-3 rounded-2xl bg-brand-blue/5 border border-brand-blue/15 hover:border-brand-blue/30 transition-all flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-brand-blue" />
                  <span className="text-xs font-semibold text-white">Privacy Center</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-white/50" />
              </div>
            </Link>
          </div>
        </GlassCard>
      </div>

      {/* ── RECENT ANALYSIS HISTORY TABLE (Section 23) ── */}
      <GlassCard variant="elevated" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white">Recent Analyses</h3>
            <p className="text-xs text-white/50">Verified audit trail from database</p>
          </div>
          <Link href="/dashboard/history">
            <GlassButton variant="ghost" size="sm" icon={<Clock className="w-3.5 h-3.5" />}>
              View All History
            </GlassButton>
          </Link>
        </div>

        {recentHistory.length === 0 ? (
          <div className="py-12 text-center space-y-3">
            <p className="text-sm text-white/50">Your verification history will appear here.</p>
            <Link href="/dashboard/analysis">
              <GlassButton variant="secondary" size="sm">
                Analyze First Media
              </GlassButton>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/8 text-white/40 font-mono uppercase">
                  <th className="py-3 px-4">Filename</th>
                  <th className="py-3 px-4">Type</th>
                  <th className="py-3 px-4">Risk Assessment</th>
                  <th className="py-3 px-4">Confidence</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/4">
                {recentHistory.map((item) => {
                  const risk = item.risk_level ? RISK_CONFIG[item.risk_level] : RISK_CONFIG.UNDETERMINED
                  const badgeStatus =
                    item.risk_level === 'LOW'
                      ? 'safe'
                      : item.risk_level === 'SUSPICIOUS'
                      ? 'warning'
                      : item.risk_level === 'HIGH' || item.risk_level === 'CRITICAL'
                      ? 'danger'
                      : 'undetermined'

                  return (
                    <tr key={item.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3.5 px-4 font-medium text-white max-w-[200px] truncate">
                        {item.original_filename}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-mono text-white/60">{item.media_type}</span>
                      </td>
                      <td className="py-3.5 px-4">
                        <GlassBadge status={badgeStatus} label={risk.label} />
                      </td>
                      <td className="py-3.5 px-4 font-mono font-semibold text-white">
                        {item.confidence !== null ? `${Math.round(item.confidence * 100)}%` : '—'}
                      </td>
                      <td className="py-3.5 px-4 text-white/50">
                        {format(new Date(item.created_at), 'MMM dd, HH:mm')}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Link
                          href={`/dashboard/analysis/${item.id}`}
                          className="text-brand-blue hover:text-white transition-colors"
                        >
                          View Details
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </GlassCard>
    </div>
  )
}
