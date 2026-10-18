'use client'
import React, { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard,
  Camera,
  UploadCloud,
  Clock,
  FileText,
  ShieldCheck,
  Bell,
  User as UserIcon,
  LogOut,
  Key,
  Shield,
  ExternalLink,
  ChevronDown,
  Sparkles,
  ShieldAlert,
} from 'lucide-react'
import clsx from 'clsx'
import Cookies from 'js-cookie'
import { BrandLogo } from './BrandLogo'
import { useAuth } from '@/contexts/AuthContext'

interface NavItem {
  href: string
  label: string
  icon: React.ElementType
  badge?: string
}

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/live-scan', label: 'Live Scan', icon: Camera, badge: 'LIVE' },
  { href: '/dashboard/analysis', label: 'Analyze', icon: UploadCloud },
  { href: '/dashboard/history', label: 'History', icon: Clock },
  { href: '/dashboard/reports', label: 'Reports', icon: FileText },
  { href: '/dashboard/privacy', label: 'Privacy', icon: ShieldCheck },
]

export const GlassNavbar: React.FC = () => {
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout } = useAuth()
  const [profileOpen, setProfileOpen] = useState(false)
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  const profileRef = useRef<HTMLDivElement>(null)
  const notifRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false)
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotificationsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = async () => {
    setProfileOpen(false)
    await logout()
  }

  return (
    <>
      {/* ── Top Floating Frosted Glass Navbar (Desktop & Tablet) ── */}
      <header className="fixed top-4 left-0 right-0 z-50 px-4 md:px-8 max-w-7xl mx-auto pointer-events-none">
        <div className="pointer-events-auto flex items-center justify-between px-5 py-3 rounded-3xl glass-floating border border-white/12 backdrop-blur-2xl shadow-glass-floating">
          {/* Brand Logo */}
          <BrandLogo href="/dashboard" size="sm" />

          {/* Navigation Links (Desktop) */}
          <nav className="hidden md:flex items-center gap-1 bg-white/[0.03] p-1 rounded-2xl border border-white/6 backdrop-blur-md">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname?.startsWith(item.href))
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={clsx(
                    'relative flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-medium tracking-wide transition-all duration-200 select-none',
                    isActive
                      ? 'text-white bg-white/10 shadow-sm border border-white/15'
                      : 'text-white/60 hover:text-white hover:bg-white/5 border border-transparent'
                  )}
                >
                  <Icon className={clsx('w-3.5 h-3.5', isActive ? 'text-brand-blue' : 'text-white/50')} />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="text-[9px] px-1.5 py-0.2 rounded-full font-mono bg-status-safe/20 text-status-safe border border-status-safe/30 animate-pulse">
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
            {user?.role === 'ADMIN' && (
              <Link
                href="/dashboard/admin"
                className={clsx(
                  'relative flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold tracking-wide transition-all duration-200 select-none',
                  pathname?.startsWith('/dashboard/admin')
                    ? 'text-white bg-brand-violet/20 shadow-sm border border-brand-violet/30'
                    : 'text-brand-violet/80 hover:text-white hover:bg-brand-violet/10 border border-transparent'
                )}
              >
                <ShieldAlert className="w-3.5 h-3.5 text-brand-violet" />
                <span>Admin</span>
                <span className="text-[9px] px-1.5 py-0.2 rounded-full font-mono bg-brand-violet/20 text-brand-violet border border-brand-violet/30">
                  OPS
                </span>
              </Link>
            )}
          </nav>

          {/* Right Action Controls */}
          <div className="flex items-center gap-2.5">
            {/* Live Operational Status Pill */}
            <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-status-safe/10 border border-status-safe/20">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-status-safe opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-status-safe" />
              </span>
              <span className="text-[11px] font-semibold tracking-wider text-status-safe uppercase">
                Active Protection
              </span>
            </div>

            {/* Notifications Dropdown */}
            <div className="relative" ref={notifRef}>
              <button
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                className="w-9 h-9 rounded-2xl flex items-center justify-center bg-white/5 border border-white/10 text-white/70 hover:text-white hover:bg-white/10 transition-all"
                aria-label="Notifications"
              >
                <Bell className="w-4 h-4" />
                <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-brand-blue" />
              </button>

              {notificationsOpen && (
                <div className="absolute right-0 mt-3 w-80 p-4 rounded-3xl glass-floating border border-white/15 shadow-glass-floating z-50">
                  <div className="flex items-center justify-between pb-3 border-b border-white/8">
                    <span className="text-xs font-semibold uppercase tracking-wider text-white">
                      Notifications
                    </span>
                    <span className="text-[11px] text-brand-blue">All Caught Up</span>
                  </div>
                  <div className="py-4 space-y-3">
                    <div className="p-3 rounded-2xl bg-white/5 border border-white/8 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-white">Real-Time Engine Online</span>
                        <span className="text-[10px] text-white/40">Just now</span>
                      </div>
                      <p className="text-white/60 text-[11px]">
                        YuNet, Celeb-DF v2, and Fourier PAD inference streams are active.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Profile Dropdown */}
            <div className="relative" ref={profileRef}>
              <button
                onClick={() => setProfileOpen(!profileOpen)}
                className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-2xl bg-white/5 border border-white/10 text-white/80 hover:text-white hover:bg-white/10 transition-all"
              >
                <div className="w-6 h-6 rounded-xl bg-gradient-to-br from-brand-blue to-brand-violet flex items-center justify-center text-xs font-bold text-white shadow-sm">
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : (user?.email ? user.email.charAt(0).toUpperCase() : 'P')}
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-white/50" />
              </button>

              {profileOpen && (
                <div className="absolute right-0 mt-3 w-56 p-2 rounded-3xl glass-floating border border-white/15 shadow-glass-floating z-50">
                  <div className="px-3 py-2.5 border-b border-white/8">
                    <p className="text-xs font-semibold text-white truncate">
                      {user?.full_name || user?.email || 'Authenticated User'}
                    </p>
                    <p className="text-[10px] text-brand-blue font-mono mt-0.5 truncate">
                      {user?.email || 'Active Session'} • {user?.role || 'USER'}
                    </p>
                  </div>
                  <div className="py-1.5 space-y-0.5">
                    <Link
                      href="/dashboard/privacy"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-white/70 hover:text-white hover:bg-white/5 transition-all"
                    >
                      <Shield className="w-3.5 h-3.5 text-brand-blue" />
                      <span>Privacy Center</span>
                    </Link>
                    <Link
                      href="/dashboard/security"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-white/70 hover:text-white hover:bg-white/5 transition-all"
                    >
                      <ShieldCheck className="w-3.5 h-3.5 text-status-safe" />
                      <span>Security Center</span>
                    </Link>
                    <Link
                      href="/dashboard/developer"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-white/70 hover:text-white hover:bg-white/5 transition-all"
                    >
                      <Key className="w-3.5 h-3.5 text-brand-violet" />
                      <span>API & Developers</span>
                    </Link>
                    <Link
                      href="/dashboard/assistant"
                      onClick={() => setProfileOpen(false)}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-white/70 hover:text-white hover:bg-white/5 transition-all"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-brand-cyan" />
                      <span>AI Security Assistant</span>
                    </Link>
                    {user?.role === 'ADMIN' && (
                      <Link
                        href="/dashboard/admin"
                        onClick={() => setProfileOpen(false)}
                        className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-brand-violet hover:text-white hover:bg-brand-violet/15 transition-all font-semibold"
                      >
                        <ShieldAlert className="w-3.5 h-3.5 text-brand-violet" />
                        <span>Admin Console</span>
                      </Link>
                    )}
                  </div>
                  <div className="pt-1.5 border-t border-white/8">
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-status-danger/80 hover:text-status-danger hover:bg-status-danger/10 transition-all text-left"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* ── Mobile Bottom Navigation Bar (< 768px) ── */}
      <div className="md:hidden fixed bottom-3 left-3 right-3 z-50 pointer-events-none">
        <div className="pointer-events-auto flex items-center justify-around p-2 rounded-3xl glass-floating border border-white/15 backdrop-blur-2xl shadow-glass-floating">
          {NAV_ITEMS.slice(0, 5).map((item) => {
            const isActive = pathname === item.href
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  'flex flex-col items-center gap-1 p-2 rounded-2xl transition-all',
                  isActive ? 'text-brand-blue bg-white/10' : 'text-white/50 hover:text-white'
                )}
              >
                <Icon className="w-4 h-4" />
                <span className="text-[10px] font-medium">{item.label}</span>
              </Link>
            )
          })}
        </div>
      </div>
    </>
  )
}

export default GlassNavbar
