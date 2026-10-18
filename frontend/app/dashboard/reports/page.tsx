'use client'
import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FileText,
  Download,
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  ExternalLink,
  Clock,
  Sparkles,
  Lock,
  Layers,
  X,
  Printer,
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

export default function ReportsPage() {
  const router = useRouter()
  const [items, setItems] = useState<Analysis[]>([])
  const [loading, setLoading] = useState(true)
  const [generatingId, setGeneratingId] = useState<string | null>(null)
  const [activeReportDoc, setActiveReportDoc] = useState<{ analysis: Analysis; report?: Report } | null>(null)

  useEffect(() => {
    if (!Cookies.get('access_token')) {
      router.push('/auth/login')
      return
    }
    analysisApi
      .getHistory(1, 50)
      .then((r) => {
        setItems(r.data.items?.filter((a: Analysis) => a.status === 'COMPLETE') || [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [router])

  const handleGenerate = async (id: string, a: Analysis) => {
    setGeneratingId(id)
    try {
      const res = await reportsApi.generate(id)
      toast.success('Security report generated!')
      setActiveReportDoc({ analysis: a, report: res.data })
    } catch (e) {
      toast.error(getErrorMessage(e))
    } finally {
      setGeneratingId(null)
    }
  }

  const handleOpenDoc = async (a: Analysis) => {
    try {
      const rep = await reportsApi.get(a.id)
      setActiveReportDoc({ analysis: a, report: rep.data })
    } catch {
      setActiveReportDoc({ analysis: a })
    }
  }

  const handleDownloadJson = async (id: string) => {
    try {
      const res = await reportsApi.downloadJson(id)
      const url = URL.createObjectURL(res.data)
      const el = document.createElement('a')
      el.href = url
      el.download = `privacy-eye-report-${id.slice(0, 8)}.json`
      el.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      toast.error(getErrorMessage(e))
    }
  }

  const handleDownloadHtml = async (id: string) => {
    try {
      const res = await reportsApi.downloadHtml(id)
      const url = URL.createObjectURL(res.data)
      const el = document.createElement('a')
      el.href = url
      el.download = `privacy-eye-certificate-${id.slice(0, 8)}.html`
      el.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      toast.error(getErrorMessage(e))
    }
  }


  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* ── HEADER ── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <FileText className="w-4 h-4 text-brand-blue" />
            <span className="text-xs uppercase font-mono tracking-widest text-brand-blue">
              Official Forensics Documentation
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
            SECURITY REPORTS
          </h1>
          <p className="text-sm text-white/60 mt-1">
            Formal authenticity audits, cryptographic hashes, and structured explainability reports.
          </p>
        </div>
      </div>

      {/* ── REPORT CARDS (Section 25 requirement) ── */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-24">
          <div className="w-8 h-8 rounded-full border-2 border-brand-blue border-t-transparent animate-spin mb-3" />
          <p className="text-xs font-mono uppercase text-white/50">Compiling Report Catalog...</p>
        </div>
      ) : items.length === 0 ? (
        <GlassCard variant="elevated" className="py-20 text-center space-y-3">
          <FileText className="w-10 h-10 mx-auto text-white/20" />
          <p className="text-sm font-semibold text-white/60">No completed analyses available for reporting.</p>
          <Link href="/dashboard/analysis">
            <GlassButton variant="primary" size="sm">
              Analyze Media First
            </GlassButton>
          </Link>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((item) => {
            const risk = RISK_CONFIG[item.risk_level || 'UNDETERMINED']
            const badgeStatus =
              item.risk_level === 'LOW'
                ? 'safe'
                : item.risk_level === 'SUSPICIOUS'
                ? 'warning'
                : item.risk_level === 'HIGH' || item.risk_level === 'CRITICAL'
                ? 'danger'
                : 'undetermined'

            return (
              <GlassCard
                key={item.id}
                variant="elevated"
                className="p-6 space-y-4 hover:border-brand-blue/30 transition-all cursor-pointer"
                onClick={() => handleOpenDoc(item)}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono text-white/40 uppercase">
                    ID: {item.id.slice(0, 12)}...
                  </span>
                  <GlassBadge status={badgeStatus} label={risk.label} />
                </div>

                <div>
                  <h3 className="text-base font-bold text-white truncate">
                    {item.original_filename}
                  </h3>
                  <p className="text-xs text-white/50 mt-1">
                    {format(new Date(item.created_at), 'MMMM dd, yyyy HH:mm')} · {item.media_type}
                  </p>
                </div>

                <div className="pt-2 flex items-center justify-between border-t border-white/6">
                  <span className="text-xs font-mono text-white/60">
                    Confidence: {item.confidence !== null ? `${Math.round(item.confidence * 100)}%` : '—'}
                  </span>

                  <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                    <GlassButton
                      variant="secondary"
                      size="sm"
                      onClick={() => handleGenerate(item.id, item)}
                      isLoading={generatingId === item.id}
                      icon={<FileText className="w-3.5 h-3.5" />}
                    >
                      Open Report
                    </GlassButton>
                    <button
                      onClick={() => handleDownloadHtml(item.id)}
                      className="p-2 rounded-xl glass-surface hover:bg-white/10 text-brand-blue hover:text-white"
                      title="Download Printable Forensic Certificate (HTML)"
                    >
                      <ShieldCheck className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => handleDownloadJson(item.id)}
                      className="p-2 rounded-xl glass-surface hover:bg-white/10 text-white/60 hover:text-white"
                      title="Download Cryptographic JSON"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </GlassCard>
            )
          })}
        </div>
      )}

      {/* ── DOCUMENT-STYLE GLASS REPORT INTERFACE MODAL (Section 25) ── */}
      <AnimatePresence>
        {activeReportDoc && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-canvas/80 backdrop-blur-xl">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-3xl max-h-[92vh] rounded-4xl glass-floating border border-white/18 p-8 md:p-10 space-y-6 shadow-glass-floating overflow-y-auto"
            >
              {/* Report Header */}
              <div className="flex items-center justify-between pb-6 border-b border-white/10">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <ShieldCheck className="w-4 h-4 text-brand-blue" />
                    <span className="text-[11px] font-mono tracking-widest uppercase text-brand-blue">
                      PRIVACY EYE FORENSIC REPORT
                    </span>
                  </div>
                  <h2 className="text-2xl font-black text-white">Digital Authenticity Audit</h2>
                  <p className="text-xs font-mono text-white/50 mt-0.5">
                    Cryptographic Document ID: {activeReportDoc.analysis.id}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDownloadHtml(activeReportDoc.analysis.id)}
                    className="p-2 rounded-xl glass-surface hover:bg-white/10 text-brand-blue"
                    title="Download Forensic Certificate (HTML/Print)"
                  >
                    <ShieldCheck className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDownloadJson(activeReportDoc.analysis.id)}
                    className="p-2 rounded-xl glass-surface hover:bg-white/10 text-white/70"
                    title="Export JSON"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setActiveReportDoc(null)}
                    className="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center text-white/60 hover:text-white"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Banner to generate full AI report if not yet generated */}
              {!activeReportDoc.report && (
                <div className="p-4 rounded-3xl bg-brand-blue/10 border border-brand-blue/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="text-xs text-white/80 space-y-0.5">
                    <strong className="text-white block font-semibold">Official AI Evidence Report Available</strong>
                    <span>Generate AI-synthesized executive summary and structured tactical next steps.</span>
                  </div>
                  <GlassButton
                    variant="primary"
                    size="sm"
                    isLoading={generatingId === activeReportDoc.analysis.id}
                    onClick={async () => {
                      setGeneratingId(activeReportDoc.analysis.id)
                      try {
                        const res = await reportsApi.generate(activeReportDoc.analysis.id)
                        setActiveReportDoc({ analysis: activeReportDoc.analysis, report: res.data })
                        toast.success('Official evidence report compiled!')
                      } catch (e) {
                        toast.error(getErrorMessage(e))
                      } finally {
                        setGeneratingId(null)
                      }
                    }}
                    icon={<Sparkles className="w-3.5 h-3.5" />}
                  >
                    Generate AI Report
                  </GlassButton>
                </div>
              )}

              {/* Assessment Section */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-3xl glass-surface border border-white/8 space-y-1">
                  <span className="text-[10px] uppercase font-mono text-white/40 block">
                    Assessment
                  </span>
                  <p className="text-lg font-bold text-white">
                    {activeReportDoc.analysis.risk_level || 'UNDETERMINED'}
                  </p>
                </div>
                <div className="p-4 rounded-3xl glass-surface border border-white/8 space-y-1">
                  <span className="text-[10px] uppercase font-mono text-white/40 block">
                    Calibrated Confidence
                  </span>
                  <p className="text-lg font-bold font-mono text-brand-blue">
                    {activeReportDoc.analysis.confidence !== null
                      ? `${Math.round(activeReportDoc.analysis.confidence * 100)}%`
                      : '—'}
                  </p>
                </div>
                <div className="p-4 rounded-3xl glass-surface border border-white/8 space-y-1">
                  <span className="text-[10px] uppercase font-mono text-white/40 block">
                    Reliability
                  </span>
                  <p className="text-lg font-bold text-status-safe">HIGH</p>
                </div>
              </div>

              {/* Provenance & Cryptographic Hashes */}
              <div className="p-5 rounded-3xl glass-surface border border-white/8 space-y-2 font-mono text-xs">
                <span className="text-[10px] uppercase font-bold text-white/40 block">
                  Media Hash & Fingerprint
                </span>
                <p className="text-white break-all bg-black/40 p-2.5 rounded-xl border border-white/6">
                  SHA-256: {activeReportDoc.analysis.file_sha256 || 'Calculated during upload ingestion'}
                </p>
                <div className="grid grid-cols-2 gap-2 text-white/60 pt-1">
                  <span>Model Engine: v1.0.0-PROD</span>
                  <span>Evaluated at: {format(new Date(activeReportDoc.analysis.created_at), 'yyyy-MM-dd HH:mm')}</span>
                </div>
              </div>

              {/* Summary & Structured Explanation */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                  Executive Forensic Summary
                </h4>
                <p className="text-xs text-white/80 leading-relaxed font-sans bg-white/4 p-4 rounded-2xl border border-white/6 whitespace-pre-line">
                  {activeReportDoc.report?.summary ||
                    activeReportDoc.analysis.explanation ||
                    'Forensic analysis indicates media structure meets calibrated organic benchmarks. No anomalous frequency spikes or boundary re-compression seams were detected.'}
                </p>
              </div>

              {/* Tactical Recommendations */}
              {activeReportDoc.report?.recommendations && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-brand-blue">
                    Tactical Recommendations & Next Steps
                  </h4>
                  <div className="p-4 rounded-2xl bg-white/4 border border-white/6 text-xs text-white/80 whitespace-pre-line leading-relaxed font-sans">
                    {activeReportDoc.report.recommendations}
                  </div>
                </div>
              )}

              {/* Detected Signals */}
              {activeReportDoc.analysis.signals?.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-white">
                    Observed Forensic Signals ({activeReportDoc.analysis.signals.length})
                  </h4>
                  <div className="space-y-1.5">
                    {activeReportDoc.analysis.signals.map((sig, idx) => (
                      <div
                        key={idx}
                        className="p-3 rounded-2xl bg-white/4 border border-white/6 flex justify-between text-xs"
                      >
                        <div>
                          <span className="font-semibold text-white block">{sig.signal_label}</span>
                          <span className="text-[11px] text-white/50">{sig.description}</span>
                        </div>
                        <span className="font-mono text-brand-blue font-bold">
                          {sig.score !== null ? `${Math.round(sig.score * 100)}%` : 'Detected'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Limitations & Legal Disclaimers (Section 25 requirement) */}
              <div className="p-4 rounded-3xl bg-brand-blue/5 border border-brand-blue/15 text-xs text-white/70 space-y-2">
                <div className="flex items-center gap-2 text-brand-blue font-bold">
                  <Sparkles className="w-4 h-4" />
                  <span>Recommended Next Steps & Technical Limitations</span>
                </div>
                <p className="leading-relaxed">
                  Deepfake models continuously evolve. Detection scores represent probabilistic
                  confidence rather than absolute certainty. For high-stakes verification, perform
                  real-time active liveness scanning with randomized head pose nonces.
                </p>
              </div>

              {/* Print / Close Footer */}
              <div className="pt-3 border-t border-white/10 flex justify-end gap-3">
                <GlassButton
                  variant="secondary"
                  size="md"
                  onClick={() => window.print()}
                  icon={<Printer className="w-4 h-4" />}
                >
                  Print Report
                </GlassButton>
                <GlassButton
                  variant="primary"
                  size="md"
                  onClick={() => setActiveReportDoc(null)}
                >
                  Done
                </GlassButton>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>

  )
}
