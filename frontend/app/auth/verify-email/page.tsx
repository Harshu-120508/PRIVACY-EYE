'use client'
import React, { useState, useEffect, Suspense } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { MailCheck, KeyRound, ArrowRight, CheckCircle2, ShieldCheck, RefreshCw, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

import { authApi, getErrorMessage } from '@/lib/api'
import { BrandLogo } from '@/components/layout/BrandLogo'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { useAuth } from '@/contexts/AuthContext'

function VerifyEmailContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, refreshUser } = useAuth()
  const queryToken = searchParams.get('token') || ''

  const [tokenInput, setTokenInput] = useState(queryToken)
  const [loading, setLoading] = useState(false)
  const [resending, setResending] = useState(false)
  const [verified, setVerified] = useState(user?.is_verified || false)
  const [devToken, setDevToken] = useState<string | null>(null)

  useEffect(() => {
    if (queryToken) {
      setTokenInput(queryToken)
      handleVerify(queryToken)
    }
  }, [queryToken])

  const handleVerify = async (tokenToUse: string) => {
    const cleanToken = tokenToUse.trim()
    if (!cleanToken) {
      toast.error('Please enter a verification token.')
      return
    }
    setLoading(true)
    try {
      await authApi.verifyEmail(cleanToken)
      setVerified(true)
      toast.success('Email successfully verified!')
      if (refreshUser) {
        await refreshUser()
      }
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const handleRequestVerification = async () => {
    setResending(true)
    try {
      const res = await authApi.requestVerification(user?.email)
      toast.success('Verification instructions generated!')
      if (res.data?.verification_token) {
        setDevToken(res.data.verification_token)
        setTokenInput(res.data.verification_token)
      }
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setResending(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-canvas relative">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-blue/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-brand-cyan/10 rounded-full blur-[100px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="flex justify-center mb-8">
          <BrandLogo size="lg" />
        </div>

        <GlassCard variant="floating" className="p-8 md:p-10 space-y-6 border border-white/14">
          <div className="text-center space-y-1">
            <span className="text-xs uppercase font-mono tracking-widest text-brand-cyan">
              Trust & Identity
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white">Verify Work Email</h1>
            <p className="text-xs text-white/50">
              Confirm your email identity to unlock complete deepfake analysis reports and audit access
            </p>
          </div>

          {verified ? (
            <div className="space-y-4 py-4 text-center">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-status-safe/10 border border-status-safe/30 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-status-safe" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-white">Email Identity Confirmed</h3>
                <p className="text-xs text-white/70 leading-relaxed">
                  Your identity has been verified. You now have full access to platform features, analysis reports, and developer tooling.
                </p>
              </div>
              <Link href="/dashboard" className="block pt-2">
                <GlassButton variant="primary" size="md" className="w-full shadow-glow-blue">
                  Enter Dashboard
                </GlassButton>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-white/70">
                  Verification Token
                </label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                  <input
                    type="text"
                    value={tokenInput}
                    onChange={(e) => setTokenInput(e.target.value)}
                    placeholder="Enter or paste verification token"
                    className="glass-input pl-11 text-xs font-mono"
                  />
                </div>
              </div>

              {devToken && (
                <div className="p-3 rounded-2xl bg-brand-blue/10 border border-brand-blue/20 text-xs text-brand-cyan space-y-1">
                  <div className="flex items-center gap-1.5 font-semibold text-[11px]">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Development Token Generated</span>
                  </div>
                  <p className="font-mono text-[10px] break-all opacity-80">{devToken}</p>
                </div>
              )}

              <GlassButton
                type="button"
                variant="primary"
                size="lg"
                onClick={() => handleVerify(tokenInput)}
                isLoading={loading}
                className="w-full shadow-glow-blue"
                icon={<ArrowRight className="w-4 h-4" />}
              >
                Verify Identity
              </GlassButton>

              <div className="pt-2 flex items-center justify-between">
                <button
                  type="button"
                  onClick={handleRequestVerification}
                  disabled={resending}
                  className="flex items-center gap-1.5 text-xs text-brand-blue hover:text-brand-cyan transition-colors"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${resending ? 'animate-spin' : ''}`} />
                  <span>{resending ? 'Generating...' : 'Request New Token'}</span>
                </button>
                <Link href="/dashboard" className="text-xs text-white/50 hover:text-white">
                  Skip for Now
                </Link>
              </div>
            </div>
          )}

          <div className="pt-4 border-t border-white/6 text-center text-xs text-white/50">
            Need to switch accounts?{' '}
            <Link href="/auth/login" className="text-brand-blue font-semibold hover:underline">
              Sign In
            </Link>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-canvas text-white/50 text-xs font-mono">
        Validating Security Identity...
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  )
}
