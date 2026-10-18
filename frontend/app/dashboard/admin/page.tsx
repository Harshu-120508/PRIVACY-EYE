'use client'
import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  ShieldAlert,
  Users,
  Layers,
  Activity,
  Search,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  UserCheck,
  UserX,
  Shield,
  FileText,
  Clock,
  Server,
  Cpu,
  Database,
  Lock,
  ChevronRight,
  Filter,
} from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

import { adminApi, getErrorMessage } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'

interface AdminStats {
  total_users: number
  active_users: number
  verified_users: number
  total_scans: number
  scans_by_risk: Record<string, number>
  scans_by_media: Record<string, number>
  total_reports: number
  active_sessions: number
  system_status: {
    database: string
    ml_pipeline: string
    active_models: string[]
    fallback_mode: boolean
  }
}

interface AdminUserItem {
  id: string
  email: string
  full_name: string | null
  role: string
  is_active: boolean
  is_verified: boolean
  scans_used_this_month: number
  scans_limit: number
  total_scans: number
  created_at: string
}

interface AdminScanItem {
  id: string
  user_id: string
  user_email: string
  original_filename: string
  media_type: string
  file_size_bytes: number
  status: string
  risk_level: string
  synthetic_probability: number | null
  confidence: number | null
  created_at: string
}

interface AdminAuditLogItem {
  id: string
  user_id: string | null
  user_email: string
  action: string
  ip_address: string | null
  user_agent: string | null
  detail: any
  created_at: string
}

export default function AdminDashboardPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'scans' | 'logs'>('overview')
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [users, setUsers] = useState<AdminUserItem[]>([])
  const [totalUsers, setTotalUsers] = useState(0)
  const [scans, setScans] = useState<AdminScanItem[]>([])
  const [totalScans, setTotalScans] = useState(0)
  const [logs, setLogs] = useState<AdminAuditLogItem[]>([])
  const [totalLogs, setTotalLogs] = useState(0)

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  // Filters
  const [userSearch, setUserSearch] = useState('')
  const [userRoleFilter, setUserRoleFilter] = useState('')
  const [userStatusFilter, setUserStatusFilter] = useState('')
  const [scanRiskFilter, setScanRiskFilter] = useState('')
  const [scanMediaFilter, setScanMediaFilter] = useState('')

  const isAdmin = user?.role === 'ADMIN'

  const loadData = async () => {
    if (!isAdmin) return
    setRefreshing(true)
    try {
      if (activeTab === 'overview') {
        const res = await adminApi.getStats()
        setStats(res.data)
      } else if (activeTab === 'users') {
        const res = await adminApi.getUsers({
          q: userSearch || undefined,
          role: userRoleFilter || undefined,
          status: userStatusFilter || undefined,
        })
        setUsers(res.data.items || [])
        setTotalUsers(res.data.total || 0)
      } else if (activeTab === 'scans') {
        const res = await adminApi.getScans({
          risk_level: scanRiskFilter || undefined,
          media_type: scanMediaFilter || undefined,
        })
        setScans(res.data.items || [])
        setTotalScans(res.data.total || 0)
      } else if (activeTab === 'logs') {
        const res = await adminApi.getAuditLogs()
        setLogs(res.data.items || [])
        setTotalLogs(res.data.total || 0)
      }
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [activeTab, isAdmin])

  const handleToggleUserStatus = async (targetUser: AdminUserItem) => {
    if (targetUser.id === user?.id) {
      toast.error('You cannot suspend your own administrative account.')
      return
    }
    const nextStatus = !targetUser.is_active
    try {
      await adminApi.updateUserStatus(targetUser.id, nextStatus)
      toast.success(`User ${nextStatus ? 'activated' : 'suspended'}.`)
      loadData()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  const handleToggleUserRole = async (targetUser: AdminUserItem) => {
    if (targetUser.id === user?.id) {
      toast.error('You cannot change your own role.')
      return
    }
    const nextRole = targetUser.role === 'ADMIN' ? 'USER' : 'ADMIN'
    try {
      await adminApi.updateUserRole(targetUser.id, nextRole)
      toast.success(`User role changed to ${nextRole}.`)
      loadData()
    } catch (err) {
      toast.error(getErrorMessage(err))
    }
  }

  if (!isAdmin) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center">
        <GlassCard variant="floating" className="p-10 border border-status-danger/30 space-y-4">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-status-danger/10 border border-status-danger/30 flex items-center justify-center text-status-danger">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-white">Administrative Access Required</h2>
          <p className="text-xs text-white/60 max-w-md mx-auto leading-relaxed">
            This module is strictly restricted to verified platform administrators. Your authenticated account does not possess the <span className="font-mono text-status-danger">ADMIN</span> role.
          </p>
          <div className="pt-2">
            <Link href="/dashboard">
              <GlassButton variant="secondary" size="md">
                Return to Dashboard
              </GlassButton>
            </Link>
          </div>
        </GlassCard>
      </div>
    )
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* ── Page Header ── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Shield className="w-4 h-4 text-brand-blue" />
            <span className="text-xs uppercase font-mono tracking-widest text-brand-blue">
              Command & Control Center
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
            Administrative Operations
          </h1>
          <p className="text-xs text-white/50 mt-1">
            Global security management, platform telemetry, forensic audit feeds, and user access controls.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <GlassButton
            variant="secondary"
            size="sm"
            onClick={loadData}
            isLoading={refreshing}
            icon={<RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />}
          >
            Refresh Telemetry
          </GlassButton>
        </div>
      </div>

      {/* ── Navigation Tabs ── */}
      <div className="flex items-center gap-1 p-1 rounded-2xl bg-white/[0.03] border border-white/6 w-fit">
        <button
          onClick={() => setActiveTab('overview')}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition-all',
            activeTab === 'overview'
              ? 'bg-brand-blue text-white shadow-glow-blue'
              : 'text-white/60 hover:text-white hover:bg-white/5'
          )}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>System Overview</span>
        </button>

        <button
          onClick={() => setActiveTab('users')}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition-all',
            activeTab === 'users'
              ? 'bg-brand-blue text-white shadow-glow-blue'
              : 'text-white/60 hover:text-white hover:bg-white/5'
          )}
        >
          <Users className="w-3.5 h-3.5" />
          <span>User Directory</span>
        </button>

        <button
          onClick={() => setActiveTab('scans')}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition-all',
            activeTab === 'scans'
              ? 'bg-brand-blue text-white shadow-glow-blue'
              : 'text-white/60 hover:text-white hover:bg-white/5'
          )}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Global Scans</span>
        </button>

        <button
          onClick={() => setActiveTab('logs')}
          className={clsx(
            'flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold tracking-wide transition-all',
            activeTab === 'logs'
              ? 'bg-brand-blue text-white shadow-glow-blue'
              : 'text-white/60 hover:text-white hover:bg-white/5'
          )}
        >
          <Lock className="w-3.5 h-3.5" />
          <span>Security Audit Trail</span>
        </button>
      </div>

      {/* ── TAB 1: OVERVIEW ── */}
      {activeTab === 'overview' && stats && (
        <div className="space-y-6">
          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <GlassCard variant="subtle" className="p-5 border border-white/8 space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-white/50">
                Total Users
              </span>
              <p className="text-3xl font-bold text-white tracking-tight">{stats.total_users}</p>
              <div className="flex items-center gap-2 text-[10px] text-status-safe">
                <span>{stats.active_users} active</span>
                <span>•</span>
                <span>{stats.verified_users} verified</span>
              </div>
            </GlassCard>

            <GlassCard variant="subtle" className="p-5 border border-white/8 space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-white/50">
                Global Scans
              </span>
              <p className="text-3xl font-bold text-white tracking-tight">{stats.total_scans}</p>
              <p className="text-[10px] text-white/40">Multi-modal deepfake analyses</p>
            </GlassCard>

            <GlassCard variant="subtle" className="p-5 border border-white/8 space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-white/50">
                Evidence Reports
              </span>
              <p className="text-3xl font-bold text-white tracking-tight">{stats.total_reports}</p>
              <p className="text-[10px] text-white/40">Chain-of-custody artifacts</p>
            </GlassCard>

            <GlassCard variant="subtle" className="p-5 border border-white/8 space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-white/50">
                Active Sessions
              </span>
              <p className="text-3xl font-bold text-brand-blue tracking-tight">{stats.active_sessions}</p>
              <p className="text-[10px] text-status-safe flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-status-safe animate-pulse" />
                Live authenticated sessions
              </p>
            </GlassCard>
          </div>

          {/* Deepfake Threat Breakdown & System Status */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Risk Distribution */}
            <GlassCard variant="floating" className="p-6 border border-white/10 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white">Threat Detection Breakdown</h3>
                <span className="text-xs text-white/40 font-mono">Platform Aggregates</span>
              </div>

              <div className="space-y-3">
                {[
                  { key: 'LOW', label: 'Low Risk / Authentic', color: 'bg-status-safe', text: 'text-status-safe' },
                  { key: 'SUSPICIOUS', label: 'Suspicious Artifacts', color: 'bg-status-warning', text: 'text-status-warning' },
                  { key: 'HIGH', label: 'High Probability Deepfake', color: 'bg-orange-500', text: 'text-orange-400' },
                  { key: 'CRITICAL', label: 'Critical Manipulation', color: 'bg-status-danger', text: 'text-status-danger' },
                  { key: 'UNDETERMINED', label: 'Inconclusive / Low Quality', color: 'bg-white/30', text: 'text-white/50' },
                ].map((item) => {
                  const count = stats.scans_by_risk[item.key] || 0
                  const pct = stats.total_scans > 0 ? Math.round((count / stats.total_scans) * 100) : 0
                  return (
                    <div key={item.key} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className={clsx('font-medium', item.text)}>{item.label}</span>
                        <span className="text-white/60 font-mono">
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                        <div
                          className={clsx('h-full rounded-full transition-all duration-500', item.color)}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </GlassCard>

            {/* Infrastructure & Pipeline Health */}
            <GlassCard variant="floating" className="p-6 border border-white/10 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white">Engine Telemetry & Health</h3>
                <GlassBadge variant="safe">All Systems Operational</GlassBadge>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-2xl bg-white/[0.03] border border-white/6">
                  <div className="flex items-center gap-3">
                    <Database className="w-4 h-4 text-brand-blue" />
                    <div>
                      <p className="text-xs font-semibold text-white">Database Core</p>
                      <p className="text-[10px] text-white/50">SQLAlchemy 2.0 Async / Alembic</p>
                    </div>
                  </div>
                  <span className="text-xs font-mono text-status-safe uppercase font-bold">
                    {stats.system_status.database}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-2xl bg-white/[0.03] border border-white/6">
                  <div className="flex items-center gap-3">
                    <Cpu className="w-4 h-4 text-brand-violet" />
                    <div>
                      <p className="text-xs font-semibold text-white">AI / ML Pipeline</p>
                      <p className="text-[10px] text-white/50">
                        {stats.system_status.fallback_mode ? 'Forensics & Spectral Mode' : 'Hybrid Forensics + Neural ONNX'}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs font-mono text-status-safe uppercase font-bold">
                    {stats.system_status.ml_pipeline}
                  </span>
                </div>

                <div className="p-3 rounded-2xl bg-white/[0.03] border border-white/6 space-y-2">
                  <p className="text-xs font-semibold text-white">Active Neural & Forensic Models</p>
                  <div className="flex flex-wrap gap-1.5">
                    {stats.system_status.active_models.map((mod) => (
                      <span
                        key={mod}
                        className="px-2 py-0.5 rounded-lg text-[10px] font-mono bg-white/5 border border-white/10 text-white/80"
                      >
                        {mod}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </GlassCard>
          </div>
        </div>
      )}

      {/* ── TAB 2: USER DIRECTORY ── */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          {/* Search & Filter Bar */}
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
              <input
                type="text"
                placeholder="Search by user email or name..."
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadData()}
                className="glass-input pl-11 text-xs"
              />
            </div>

            <select
              value={userRoleFilter}
              onChange={(e) => {
                setUserRoleFilter(e.target.value)
                setTimeout(loadData, 50)
              }}
              className="glass-input text-xs w-full sm:w-40"
            >
              <option value="" className="bg-canvas">All Roles</option>
              <option value="USER" className="bg-canvas">User</option>
              <option value="ADMIN" className="bg-canvas">Admin</option>
              <option value="ENTERPRISE" className="bg-canvas">Enterprise</option>
            </select>

            <select
              value={userStatusFilter}
              onChange={(e) => {
                setUserStatusFilter(e.target.value)
                setTimeout(loadData, 50)
              }}
              className="glass-input text-xs w-full sm:w-40"
            >
              <option value="" className="bg-canvas">All Statuses</option>
              <option value="active" className="bg-canvas">Active Only</option>
              <option value="suspended" className="bg-canvas">Suspended Only</option>
            </select>

            <GlassButton variant="primary" size="sm" onClick={loadData}>
              Apply
            </GlassButton>
          </div>

          {/* User Table */}
          <GlassCard variant="floating" className="p-0 border border-white/10 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-white/8 bg-white/[0.02] text-white/50 uppercase tracking-wider font-mono text-[10px]">
                    <th className="px-5 py-3.5">User Identity</th>
                    <th className="px-4 py-3.5">Role</th>
                    <th className="px-4 py-3.5">Account Status</th>
                    <th className="px-4 py-3.5">Identity Verification</th>
                    <th className="px-4 py-3.5">Scans (Month / Total)</th>
                    <th className="px-4 py-3.5">Registered</th>
                    <th className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/6">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="px-5 py-3.5">
                        <div className="font-semibold text-white">{u.full_name || 'Unnamed User'}</div>
                        <div className="text-white/50 text-[11px] font-mono">{u.email}</div>
                      </td>
                      <td className="px-4 py-3.5">
                        <span
                          className={clsx(
                            'px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold uppercase',
                            u.role === 'ADMIN'
                              ? 'bg-brand-violet/20 text-brand-violet border border-brand-violet/30'
                              : u.role === 'ENTERPRISE'
                              ? 'bg-brand-cyan/20 text-brand-cyan border border-brand-cyan/30'
                              : 'bg-white/10 text-white/70 border border-white/15'
                          )}
                        >
                          {u.role}
                        </span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span
                          className={clsx(
                            'inline-flex items-center gap-1 text-[11px] font-medium',
                            u.is_active ? 'text-status-safe' : 'text-status-danger'
                          )}
                        >
                          <span
                            className={clsx(
                              'w-1.5 h-1.5 rounded-full',
                              u.is_active ? 'bg-status-safe' : 'bg-status-danger'
                            )}
                          />
                          {u.is_active ? 'Active' : 'Suspended'}
                        </span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span
                          className={clsx(
                            'inline-flex items-center gap-1 text-[11px]',
                            u.is_verified ? 'text-brand-blue' : 'text-white/40'
                          )}
                        >
                          {u.is_verified ? (
                            <>
                              <CheckCircle2 className="w-3.5 h-3.5 text-brand-blue" />
                              <span>Verified</span>
                            </>
                          ) : (
                            <span>Unverified</span>
                          )}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 font-mono text-white/70">
                        {u.scans_used_this_month} / {u.total_scans}
                      </td>
                      <td className="px-4 py-3.5 text-white/50 font-mono text-[11px]">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-5 py-3.5 text-right space-x-2">
                        {/* Toggle Role Button */}
                        <button
                          onClick={() => handleToggleUserRole(u)}
                          disabled={u.id === user?.id}
                          className="px-2.5 py-1 rounded-xl text-[10px] font-medium bg-white/5 hover:bg-white/10 text-white/80 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                          title={u.role === 'ADMIN' ? 'Demote to User' : 'Promote to Admin'}
                        >
                          {u.role === 'ADMIN' ? 'Demote' : 'Make Admin'}
                        </button>

                        {/* Toggle Status Button */}
                        <button
                          onClick={() => handleToggleUserStatus(u)}
                          disabled={u.id === user?.id}
                          className={clsx(
                            'px-2.5 py-1 rounded-xl text-[10px] font-medium transition-colors disabled:opacity-30 disabled:cursor-not-allowed',
                            u.is_active
                              ? 'bg-status-danger/10 hover:bg-status-danger/20 text-status-danger border border-status-danger/30'
                              : 'bg-status-safe/10 hover:bg-status-safe/20 text-status-safe border border-status-safe/30'
                          )}
                        >
                          {u.is_active ? 'Suspend' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-white/40 text-xs">
                        No users match the search criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </div>
      )}

      {/* ── TAB 3: GLOBAL SCANS FEED ── */}
      {activeTab === 'scans' && (
        <div className="space-y-4">
          {/* Risk & Media Filters */}
          <div className="flex items-center gap-3">
            <select
              value={scanRiskFilter}
              onChange={(e) => {
                setScanRiskFilter(e.target.value)
                setTimeout(loadData, 50)
              }}
              className="glass-input text-xs w-48"
            >
              <option value="" className="bg-canvas">All Risk Levels</option>
              <option value="LOW" className="bg-canvas">Low Risk</option>
              <option value="SUSPICIOUS" className="bg-canvas">Suspicious</option>
              <option value="HIGH" className="bg-canvas">High Risk</option>
              <option value="CRITICAL" className="bg-canvas">Critical</option>
            </select>

            <select
              value={scanMediaFilter}
              onChange={(e) => {
                setScanMediaFilter(e.target.value)
                setTimeout(loadData, 50)
              }}
              className="glass-input text-xs w-48"
            >
              <option value="" className="bg-canvas">All Media Types</option>
              <option value="IMAGE" className="bg-canvas">Image</option>
              <option value="VIDEO" className="bg-canvas">Video</option>
              <option value="AUDIO" className="bg-canvas">Audio</option>
            </select>

            <GlassButton variant="primary" size="sm" onClick={loadData}>
              Filter
            </GlassButton>
          </div>

          <GlassCard variant="floating" className="p-0 border border-white/10 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-white/8 bg-white/[0.02] text-white/50 uppercase tracking-wider font-mono text-[10px]">
                    <th className="px-5 py-3.5">Filename</th>
                    <th className="px-4 py-3.5">User</th>
                    <th className="px-4 py-3.5">Media</th>
                    <th className="px-4 py-3.5">Risk Rating</th>
                    <th className="px-4 py-3.5">Synthetic Probability</th>
                    <th className="px-4 py-3.5">Timestamp</th>
                    <th className="px-5 py-3.5 text-right">View</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/6">
                  {scans.map((s) => (
                    <tr key={s.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="px-5 py-3.5 font-medium text-white max-w-xs truncate">
                        {s.original_filename}
                      </td>
                      <td className="px-4 py-3.5 text-white/60 font-mono text-[11px]">
                        {s.user_email}
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="px-2 py-0.5 rounded-lg text-[10px] font-mono bg-white/5 border border-white/10 text-white/70">
                          {s.media_type}
                        </span>
                      </td>
                      <td className="px-4 py-3.5">
                        <span
                          className={clsx(
                            'px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold',
                            s.risk_level === 'LOW' && 'bg-status-safe/10 text-status-safe border border-status-safe/30',
                            s.risk_level === 'SUSPICIOUS' && 'bg-status-warning/10 text-status-warning border border-status-warning/30',
                            s.risk_level === 'HIGH' && 'bg-orange-500/10 text-orange-400 border border-orange-500/30',
                            s.risk_level === 'CRITICAL' && 'bg-status-danger/10 text-status-danger border border-status-danger/30',
                            s.risk_level === 'UNDETERMINED' && 'bg-white/5 text-white/40 border border-white/10'
                          )}
                        >
                          {s.risk_level}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 font-mono">
                        {s.synthetic_probability !== null
                          ? `${(s.synthetic_probability * 100).toFixed(1)}%`
                          : 'N/A'}
                      </td>
                      <td className="px-4 py-3.5 text-white/50 font-mono text-[11px]">
                        {new Date(s.created_at).toLocaleString()}
                      </td>
                      <td className="px-5 py-3.5 text-right">
                        <Link
                          href={`/dashboard/history?id=${s.id}`}
                          className="text-brand-blue hover:text-brand-cyan font-mono text-[11px]"
                        >
                          Inspect →
                        </Link>
                      </td>
                    </tr>
                  ))}
                  {scans.length === 0 && (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-white/40 text-xs">
                        No scans recorded matching filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </div>
      )}

      {/* ── TAB 4: AUDIT LOGS ── */}
      {activeTab === 'logs' && (
        <div className="space-y-4">
          <GlassCard variant="floating" className="p-0 border border-white/10 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-white/8 bg-white/[0.02] text-white/50 uppercase tracking-wider text-[10px]">
                    <th className="px-5 py-3.5">Action Code</th>
                    <th className="px-4 py-3.5">User Context</th>
                    <th className="px-4 py-3.5">IP Address</th>
                    <th className="px-4 py-3.5">Timestamp</th>
                    <th className="px-5 py-3.5">Event Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/6 text-[11px]">
                  {logs.map((l) => (
                    <tr key={l.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="px-5 py-3 text-brand-blue font-bold">
                        {l.action}
                      </td>
                      <td className="px-4 py-3 text-white/70">
                        {l.user_email}
                      </td>
                      <td className="px-4 py-3 text-white/50">
                        {l.ip_address || 'Internal/Proxy'}
                      </td>
                      <td className="px-4 py-3 text-white/40 text-[10px]">
                        {new Date(l.created_at).toLocaleString()}
                      </td>
                      <td className="px-5 py-3 text-white/60 text-[10px] max-w-sm truncate">
                        {l.detail ? JSON.stringify(l.detail) : '—'}
                      </td>
                    </tr>
                  ))}
                  {logs.length === 0 && (
                    <tr>
                      <td colSpan={5} className="text-center py-8 text-white/40 text-xs font-sans">
                        No audit records found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  )
}
