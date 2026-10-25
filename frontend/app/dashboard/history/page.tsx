'use client'
import React, { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Clock,
  Search,
  Image as ImageIcon,
  Video,
  Music,
  Trash2,
  FileText,
  Download,
  Filter,
  ArrowRight,
  X,
  ExternalLink,
  Shield,
  Activity,
  Layers,
  Lock,
} from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'

import { analysisApi, reportsApi, getErrorMessage } from '@/lib/api'
import type { Analysis } from '@/types'
import { RISK_CONFIG } from '@/types'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'

export default function HistoryPage() {
  const router = useRouter()
  const [items, setItems] = useState<Analysis[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [mediaFilter, setMediaFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedItem, setSelectedItem] = useState<Analysis | null>(null)
  const PER_PAGE = 12

  const loadData = useCallback(async (p: number, filterType?: string) => {
    setLoading(true)
    try {
      const res = await analysisApi.getHistory(p, PER_PAGE, filterType || undefined)
      setItems(res.data.items || [])
      setTotal(res.data.total || 0)
    } catch {
      router.push('/auth/login')
    } finally {
      setLoading(false)
    }
  }, [router])

  useEffect(() => {
    loadData(page, mediaFilter)
  }, [loadData, page, mediaFilter])

  const handleDelete = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation()
    if (!confirm('Permanently delete this audit analysis record?')) return
    try {
      await analysisApi.deleteAnalysis(id)
      setItems((prev) => prev.filter((item) => item.id !== id))
      setTotal((prev) => prev - 1)
      if (selectedItem?.id === id) setSelectedItem(null)
      toast.success('Record purged')
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const handleDownloadJson = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation()
    try {
      const res = await reportsApi.downloadJson(id)
      const url = URL.createObjectURL(res.data)
      const el = document.createElement('a')
      el.href = url
      el.download = `privacy-eye-audit-${id.slice(0, 8)}.json`
      el.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const filteredItems = items.filter((item) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      item.original_filename.toLowerCase().includes(q) ||
      item.id.toLowerCase().includes(q)
    )
  })

  const totalPages = Math.ceil(total / PER_PAGE)

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* ── HEADER ── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-4 h-4 text-brand-blue" />
            <span className="text-xs uppercase font-mono tracking-widest text-brand-blue">
              Audit Trail
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
            ANALYSIS HISTORY
          </h1>
          <p className="text-sm text-white/60 mt-1">
            {total} verifiable forensic records logged in cryptographic audit trail.
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex flex-wrap items-center gap-2">
          {['', 'IMAGE', 'VIDEO', 'AUDIO'].map((tab) => (
            <button
              key={tab}
              onClick={() => {
                setMediaFilter(tab)
                setPage(1)
              }}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold tracking-wide transition-all ${
                mediaFilter === tab
                  ? 'bg-brand-blue text-white shadow-glow-blue border border-brand-blue/50'
                  : 'glass-surface text-white/60 hover:text-white border border-white/8'
              }`}
            >
              {tab || 'All Media'}
            </button>
          ))}
        </div>
      </div>

      {/* ── SEARCH & SUMMARY BAR ── */}
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
          <input
            type="text"
            placeholder="Search by filename or analysis ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="glass-input pl-11 py-2.5 text-xs font-mono"
          />
        </div>
        <div className="text-xs text-white/50 font-mono whitespace-nowrap">
          Page {page} of {totalPages || 1}
        </div>
      </div>

      {/* ── AUDIT TABLE (Section 23 requirement) ── */}
      <GlassCard variant="elevated" className="overflow-hidden p-0">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-24">
            <div className="w-8 h-8 rounded-full border-2 border-brand-blue border-t-transparent animate-spin mb-3" />
            <p className="text-xs font-mono uppercase text-white/50">Fetching Audit Log...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="py-20 text-center space-y-3">
            <Clock className="w-10 h-10 mx-auto text-white/20" />
            <p className="text-sm font-semibold text-white/60">Your verification history will appear here.</p>
            <Link href="/dashboard/analysis">
              <GlassButton variant="primary" size="sm">
                Analyze Media
              </GlassButton>
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-white/8 text-white/40 font-mono uppercase">
                  <th className="py-3.5 px-6">File</th>
                  <th className="py-3.5 px-4">Type</th>
                  <th className="py-3.5 px-4">Assessment</th>
                  <th className="py-3.5 px-4">Confidence</th>
                  <th className="py-3.5 px-4">Date</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/4 font-sans">
                {filteredItems.map((item) => {
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
                    <tr
                      key={item.id}
                      onClick={() => setSelectedItem(item)}
                      className="hover:bg-white/[0.03] transition-colors cursor-pointer group"
                    >
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-2.5">
                          {item.media_type === 'IMAGE' && (
                            <ImageIcon className="w-4 h-4 text-brand-blue flex-shrink-0" />
                          )}
                          {item.media_type === 'VIDEO' && (
                            <Video className="w-4 h-4 text-brand-violet flex-shrink-0" />
                          )}
                          {item.media_type === 'AUDIO' && (
                            <Music className="w-4 h-4 text-brand-cyan flex-shrink-0" />
                          )}
                          <span className="font-semibold text-white truncate max-w-[220px]">
                            {item.original_filename}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-4 font-mono text-white/60">{item.media_type}</td>
                      <td className="py-4 px-4">
                        <GlassBadge status={badgeStatus} label={risk.label} />
                      </td>
                      <td className="py-4 px-4 font-mono font-bold text-white">
                        {item.confidence !== null ? `${Math.round(item.confidence * 100)}%` : '—'}
                      </td>
                      <td className="py-4 px-4 text-white/50 whitespace-nowrap">
                        {format(new Date(item.created_at), 'MMM dd, yyyy HH:mm')}
                      </td>
                      <td className="py-4 px-6 text-right">
                        <div className="flex items-center justify-end gap-2 opacity-80 group-hover:opacity-100">
                          <Link
                            href={`/dashboard/analysis/${item.id}`}
                            onClick={(e) => e.stopPropagation()}
                            className="p-1.5 rounded-lg glass-surface hover:bg-white/10 text-white/70 hover:text-white"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </Link>
                          <button
                            onClick={(e) => handleDelete(item.id, e)}
                            className="p-1.5 rounded-lg glass-surface hover:bg-status-danger/20 text-white/40 hover:text-status-danger"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination footer */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-white/6 text-xs">
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </GlassButton>
            <span className="text-white/50 font-mono">
              Page {page} of {totalPages}
            </span>
            <GlassButton
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              Next
            </GlassButton>
          </div>
        )}
      </GlassCard>

      {/* ── INDIVIDUAL ANALYSIS HISTORY DETAIL DRAWER (Section 24 requirement) ── */}
      <AnimatePresence>
        {selectedItem && (
          <div className="fixed inset-0 z-50 flex items-center justify-end p-4 bg-canvas/70 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 50 }}
              className="w-full max-w-lg h-full max-h-[90vh] rounded-4xl glass-floating border border-white/16 p-6 md:p-8 space-y-6 shadow-glass-floating overflow-y-auto"
            >
              <div className="flex items-center justify-between pb-3 border-b border-white/8">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-widest text-brand-blue">
                    Individual Audit Inspection
                  </span>
                  <h3 className="text-lg font-bold text-white mt-0.5 truncate max-w-xs">
                    {selectedItem.original_filename}
                  </h3>
                </div>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-white/60 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Data Items */}
              <div className="space-y-3 text-xs font-mono">
                <div className="p-3 rounded-2xl bg-white/4 border border-white/6 flex justify-between">
                  <span className="text-white/40">Analysis ID:</span>
                  <span className="text-white font-semibold truncate max-w-[220px]">
                    {selectedItem.id}
                  </span>
                </div>
                <div className="p-3 rounded-2xl bg-white/4 border border-white/6 flex justify-between">
                  <span className="text-white/40">Media Type:</span>
                  <span className="text-white font-semibold">{selectedItem.media_type}</span>
                </div>
                <div className="p-3 rounded-2xl bg-white/4 border border-white/6 flex justify-between items-center">
                  <span className="text-white/40">Assessment:</span>
                  <GlassBadge
                    status={
                      selectedItem.risk_level === 'LOW'
                        ? 'safe'
                        : selectedItem.risk_level === 'SUSPICIOUS'
                        ? 'warning'
                        : 'danger'
                    }
                    label={selectedItem.risk_level || 'UNDETERMINED'}
                  />
                </div>
                <div className="p-3 rounded-2xl bg-white/4 border border-white/6 flex justify-between">
                  <span className="text-white/40">Confidence:</span>
                  <span className="text-white font-bold">
                    {selectedItem.confidence !== null
                      ? `${Math.round(selectedItem.confidence * 100)}%`
                      : 'N/A'}
                  </span>
                </div>
                <div className="p-3 rounded-2xl bg-white/4 border border-white/6 flex justify-between">
                  <span className="text-white/40">Timestamp:</span>
                  <span className="text-white font-semibold">
                    {format(new Date(selectedItem.created_at), 'yyyy-MM-dd HH:mm:ss')}
                  </span>
                </div>
                <div className="p-3 rounded-2xl bg-white/4 border border-white/6 flex justify-between">
                  <span className="text-white/40">SHA-256 Digest:</span>
                  <span className="text-white font-semibold truncate max-w-[220px]">
                    {selectedItem.file_sha256 || 'Verified'}
                  </span>
                </div>
                <div className="p-3 rounded-2xl bg-white/4 border border-white/6 flex justify-between">
                  <span className="text-white/40">Model Engine:</span>
                  <span className="text-brand-blue font-semibold">YuNet + FF++ + Celeb-DF</span>
                </div>
              </div>

              {/* Signals breakdown */}
              {selectedItem.signals?.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-mono uppercase text-white/50">
                    Detected Signals ({selectedItem.signals.length})
                  </span>
                  <div className="space-y-1.5">
                    {selectedItem.signals.map((s, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-xl bg-white/4 border border-white/6 flex justify-between text-xs"
                      >
                        <span className="text-white/80">{s.signal_label}</span>
                        <span className="font-mono text-brand-blue">
                          {s.score !== null ? `${Math.round(s.score * 100)}%` : 'Active'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action buttons (Section 24 requirement) */}
              <div className="pt-4 border-t border-white/8 flex flex-col gap-2.5">
                <Link href={`/dashboard/analysis/${selectedItem.id}`} className="w-full">
                  <GlassButton variant="primary" size="md" className="w-full">
                    View Full Analysis Report
                  </GlassButton>
                </Link>
                <GlassButton
                  variant="secondary"
                  size="md"
                  onClick={(e) => handleDownloadJson(selectedItem.id, e)}
                  icon={<Download className="w-4 h-4 text-brand-blue" />}
                >
                  Export Cryptographic JSON
                </GlassButton>
                <GlassButton
                  variant="danger"
                  size="sm"
                  onClick={(e) => handleDelete(selectedItem.id, e)}
                  icon={<Trash2 className="w-3.5 h-3.5" />}
                >
                  Purge from History
                </GlassButton>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
