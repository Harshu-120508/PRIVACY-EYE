import React from 'react'
import Link from 'next/link'
import { BrandLogo } from './BrandLogo'

export const Footer: React.FC = () => {
  return (
    <footer className="relative z-10 border-t border-white/6 py-12 px-6 md:px-12 mt-20 backdrop-blur-md">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex flex-col items-center md:items-start gap-1">
          <BrandLogo size="sm" />
          <p className="text-xs text-white/40 mt-1">
            Digital Authenticity Infrastructure · Real ML Inference
          </p>
        </div>

        <nav className="flex flex-wrap items-center justify-center gap-6 text-xs text-white/50">
          <Link href="/privacy" className="hover:text-white transition-colors">
            Privacy Policy
          </Link>
          <Link href="/dashboard/privacy" className="hover:text-white transition-colors">
            Privacy Center
          </Link>
          <Link href="/dashboard/security" className="hover:text-white transition-colors">
            Security
          </Link>
          <Link href="/dashboard/developer" className="hover:text-white transition-colors">
            API & Docs
          </Link>
          <Link href="/dashboard/reports" className="hover:text-white transition-colors">
            Reports
          </Link>
          <span className="text-white/20">|</span>
          <span className="text-white/30 font-mono text-[11px]">v1.0.0-PROD</span>
        </nav>
      </div>
    </footer>
  )
}

export default Footer
