'use client'
import React, { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { GlassNavbar } from '@/components/layout/GlassNavbar'
import { Footer } from '@/components/layout/Footer'
import { Eye } from 'lucide-react'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const { isAuthenticated, isLoading } = useAuth()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      const target = pathname ? `/auth/login?next=${encodeURIComponent(pathname)}` : '/auth/login'
      router.push(target)
    }
  }, [isAuthenticated, isLoading, pathname, router])

  if (isLoading || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-canvas">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 rounded-2xl glass-card flex items-center justify-center border border-white/20 shadow-[0_0_20px_rgba(255,255,255,0.15)] animate-pulse">
            <Eye className="w-6 h-6 text-white" />
          </div>
          <p className="text-xs uppercase tracking-widest text-white/50 font-mono">
            Securing Session...
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-canvas text-white selection:bg-white/25">
      <GlassNavbar />
      <main className="flex-1 pt-28 pb-16 px-4 md:px-8 max-w-7xl mx-auto w-full">
        {children}
      </main>
      <Footer />
    </div>
  )
}
