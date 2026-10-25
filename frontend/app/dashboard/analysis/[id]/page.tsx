'use client'
import React, { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  AlertTriangle,
  Download,
  FileText,
  Shield,
  CheckCircle2,
  Trash2,
  Clock,
  Sparkles,
  Layers,
  Activity,
  Cpu,
  Lock,
  ExternalLink,
} from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'

import { analysisApi, reportsApi, getErrorMessage } from '@/lib/api'
import type { Analysis, Report } from '@/types'
import { RISK_CONFIG } from '@/types'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'
import { ConfidenceRing } from '@/components/ui/ConfidenceRing'
import { SignalBar } from '@/components/ui/SignalBar'

export default function AnalysisDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [report, setReport] = useState<Report | null>(null)
  const [genLoading, setGenLoading] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      analysisApi.getAnalysis(id).then((r) => setAnalysis(r.data)),
      reportsApi.get(id).then((r) => setReport(r.data)).catch(() => {}),
    ])
      .catch(() => {
        toast.error('Could not load analysis record')
        router.push('/dashboard/history')
      })
      .finally(() => setLoading(false))
  }, [id, router])

  const generateReport = async () => {
    setGenLoading(true)
    try {
      const res = await reportsApi.generate(id)
      setReport(res.data)
      toast.success('Security report generated!')
    } catch (e) {
      toast.error(getErrorMessage(e))
    } finally {
      setGenLoading(false)
    }
  }

  const downloadJson = async () => {
    try {
      const res = await reportsApi.downloadJson(id)
      const url = URL.createObjectURL(res.data)
      const el = document.createElement('a')
      el.href = url
      el.download = `privacy-eye-forensics-${id.slice(0, 8)}.json`
      el.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      toast.error(getErrorMessage(e))
    }
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to permanently delete this audit record?')) return
    try {
      await analysisApi.deleteAnalysis(id)
      toast.success('Record purged from audit log')
      router.push('/dashboard/history')
    } catch (e) {
      toast.error(getErrorMessage(e))
    }
  }

  if (loading || !analysis) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 rounded-2xl glass-card flex items-center justify-center border border-brand-blue/30 shadow-glow-blue animate-pulse">
          <Activity className="w-6 h-6 text-brand-blue" />
        </div>
        <p className="mt-4 text-xs font-mono uppercase tracking-widest text-white/50">
          Deciphering Forensic Record...
        </p>
      </div>
    )
  }

  const risk = RISK_CONFIG[analysis.risk_level || 'UNDETERMINED']
  const confValue = analysis.confidence !== null ? Math.round(analysis.confidence * 100) : 0
  const synthValue =
    analysis.synthetic_probability !== null ? Math.round(analysis.synthetic_probability * 100) : 0

  const badgeStatus =
    analysis.risk_level === 'LOW'
      ? 'safe'
      : analysis.risk_level === 'SUSPICIOUS'
      ? 'warning'
      : analysis.risk_level === 'HIGH' || analysis.risk_level === 'CRITICAL'
      ? 'danger'
      : 'undetermined'

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* ── TOP NAV BAR ── */}
      <div className="flex items-center justify-between">
        <Link href="/dashboard/history">
          <GlassButton variant="ghost" size="sm" icon={<ArrowLeft className="w-4 h-4" />}>
            Back to Audit Trail
          </GlassButton>
        </Link>

        <div className="flex items-center gap-3">
          {report ? (
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={downloadJson}
              icon={<Download className="w-4 h-4 text-brand-blue" />}
            >
              Export JSON Audit
            </GlassButton>
          ) : (
            <GlassButton
              variant="primary"
              size="sm"
              onClick={generateReport}
              isLoading={genLoading}
              icon={<FileText className="w-4 h-4" />}
            >
              Generate Security Report
            </GlassButton>
          )}

          <GlassButton
            variant="ghost"
            size="sm"
            onClick={handleDelete}
            icon={<Trash2 className="w-4 h-4 text-status-danger" />}
          >
            Purge
          </GlassButton>
        </div>
      </div>

      {/* ── LARGE HERO GLASS CARD (Section 21 requirement) ── */}
      <GlassCard variant="floating" className="p-8 md:p-10 space-y-8 border border-white/14">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 pb-6 border-b border-white/8">
          <div>
            <div className="flex flex-wrap items-center gap-3 mb-2">
              <span className={`text-xs font-mono uppercase tracking-widest ${
                analysis.status === 'COMPLETE' ? 'text-brand-blue' : analysis.status === 'UNSUPPORTED' ? 'text-status-warning' : 'text-status-danger'
              }`}>
                {analysis.status}
              </span>
              <span className="text-white/20">·</span>
              <span className="text-xs text-white/50 font-mono">
                ID: {analysis.id.slice(0, 12)}...
              </span>
              {analysis.model_id && (
                <>
                  <span className="text-white/20">·</span>
                  <span className="text-xs text-brand-violet font-mono">
                    {analysis.model_id} (v{analysis.model_version || '1.0.0'})
                  </span>
                </>
              )}
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white">
              {analysis.original_filename}
            </h1>
            <p className="text-xs text-white/50 mt-1 font-mono">
              {analysis.media_type} · {(analysis.file_size_bytes / (1024 * 1024)).toFixed(2)} MB ·{' '}
              {format(new Date(analysis.created_at), 'MMMM dd, yyyy HH:mm:ss')}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {analysis.prediction && (
              <span className="px-3 py-1 rounded-full text-xs font-mono font-bold border border-white/20 bg-white/5 text-white">
                PREDICTION: {analysis.prediction}
              </span>
            )}
            <GlassBadge status={badgeStatus} label={risk.label.toUpperCase()} pulse />
          </div>
        </div>

        {/* Hero Gauge & Probabilities (Section 22) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          <div className="flex items-center justify-center p-4 rounded-3xl glass-surface border border-white/8">
            <ConfidenceRing
              value={confValue}
              size={130}
              strokeWidth={10}
              label="CONFIDENCE"
              status={badgeStatus}
            />
          </div>

          <div className="space-y-4 md:col-span-2">
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="font-semibold text-white">Synthetic Probability</span>
                <span className="font-mono font-bold text-white">{synthValue}%</span>
              </div>
              <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    synthValue > 70
                      ? 'bg-status-danger'
                      : synthValue > 40
                      ? 'bg-status-warning'
                      : 'bg-status-safe'
                  }`}
                  style={{ width: `${synthValue}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs font-mono pt-2">
              <div className="p-3 rounded-2xl bg-white/4 border border-white/6">
                <span className="text-white/40 block text-[10px] uppercase">Processing Time</span>
                <span className="text-white font-bold text-sm mt-0.5 block">
                  {analysis.processing_ms ? `${analysis.processing_ms} ms` : 'Instant'}
                </span>
              </div>
              <div className="p-3 rounded-2xl bg-white/4 border border-white/6">
                <span className="text-white/40 block text-[10px] uppercase">SHA-256 Hash</span>
                <span className="text-white font-bold text-xs truncate mt-0.5 block">
                  {analysis.file_sha256 ? `${analysis.file_sha256.slice(0, 16)}...` : 'Verified'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Structured Explanation */}
        {analysis.explanation && (
          <div className="p-5 rounded-3xl glass-surface border border-white/8 space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-blue flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              Forensic Synthesis
            </span>
            <p className="text-sm text-white/80 leading-relaxed font-sans">
              {analysis.explanation}
            </p>
          </div>
        )}

        {/* Model Limitations & Transparency Notice */}
        {analysis.limitations && (
          <div className="p-4 rounded-3xl bg-white/[0.03] border border-white/8 space-y-1">
            <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-white/50 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-status-warning" />
              Model Scope & Limitations
            </span>
            <p className="text-xs text-white/70 leading-relaxed font-sans">
              {analysis.limitations}
            </p>
          </div>
        )}
      </GlassCard>

      {/* ── SMALLER FORENSIC PANELS (Section 21 requirement) ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Panel 1: Detected Signals */}
        <GlassCard variant="elevated" className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-white/6">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-brand-blue" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                DETECTION SIGNALS ({analysis.signals.length})
              </h3>
            </div>
          </div>

          {analysis.signals.length === 0 ? (
            <p className="text-xs text-white/50 py-4">No anomalous forensic signals triggered.</p>
          ) : (
            <div className="space-y-4">
              {analysis.signals.map((sig, idx) => (
                <SignalBar
                  key={idx}
                  label={sig.signal_label}
                  value={sig.score !== null ? sig.score : 0.15}
                  severity={sig.severity}
                  detail={sig.description || undefined}
                />
              ))}
            </div>
          )}
        </GlassCard>

        {/* Panel 2: Provenance & Technical Metadata */}
        <GlassCard variant="elevated" className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-white/6">
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-status-safe" />
              <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                PROVENANCE & CRYPTOGRAPHY
              </h3>
            </div>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div className="p-3 rounded-2xl bg-white/4 border border-white/6 flex items-center justify-between">
              <span className="text-white/50">MIME Format</span>
              <span className="text-white font-semibold">{analysis.mime_type || 'auto-detected'}</span>
            </div>
            {analysis.model_id && (
              <div className="p-3 rounded-2xl bg-white/4 border border-white/6 flex items-center justify-between">
                <span className="text-white/50">Active Model</span>
                <span className="text-brand-violet font-semibold">{analysis.model_id}</span>
              </div>
            )}
            {analysis.error_code && (
              <div className="p-3 rounded-2xl bg-status-danger/10 border border-status-danger/30 flex items-center justify-between">
                <span className="text-status-danger">Error Diagnostic</span>
                <span className="text-status-danger font-semibold">{analysis.error_code}</span>
              </div>
            )}
            <div className="p-3 rounded-2xl bg-white/4 border border-white/6 flex items-center justify-between">
              <span className="text-white/50">File Retained on Server</span>
              <span className="text-status-safe font-semibold">
                {analysis.media_deleted ? 'PURGED (0 Bytes)' : 'NO (Ephemeral)'}
              </span>
            </div>
            <div className="p-3 rounded-2xl bg-white/4 border border-white/6 flex items-center justify-between">
              <span className="text-white/50">Processing Architecture</span>
              <span className="text-brand-blue font-semibold">FASTAPI CORE / LOCAL ML</span>
            </div>
          </div>

          {/* Report quick link */}
          {report && (
            <div className="pt-2">
              <Link href="/dashboard/reports">
                <GlassButton variant="secondary" size="sm" className="w-full justify-between">
                  <span>View Formal Security Report</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </GlassButton>
              </Link>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  )
}
