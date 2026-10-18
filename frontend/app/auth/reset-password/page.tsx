'use client'
import React, { useState, useEffect, Suspense } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { Lock, KeyRound, ArrowRight, CheckCircle2, ShieldCheck, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'

import { authApi, getErrorMessage } from '@/lib/api'
import { BrandLogo } from '@/components/layout/BrandLogo'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'

interface ResetForm {
  token: string
  new_password: string
  confirm_password: string
}

function ResetPasswordContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const queryToken = searchParams.get('token') || ''

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<ResetForm>({
    defaultValues: {
      token: queryToken,
      new_password: '',
      confirm_password: '',
    },
  })

  useEffect(() => {
    if (queryToken) {
      setValue('token', queryToken)
    }
  }, [queryToken, setValue])

  const newPassword = watch('new_password') || ''

  // Live password validation checklist
  const hasMinLen = newPassword.length >= 8
  const hasUpper = /[A-Z]/.test(newPassword)
  const hasDigit = /[0-9]/.test(newPassword)

  const onSubmit = async (data: ResetForm) => {
    if (data.new_password !== data.confirm_password) {
      toast.error('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      await authApi.resetPassword(data.token, data.new_password, data.confirm_password)
      setSubmitted(true)
      toast.success('Password updated successfully!')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-canvas relative">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-blue/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-brand-violet/10 rounded-full blur-[100px] pointer-events-none" />

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
            <span className="text-xs uppercase font-mono tracking-widest text-brand-blue">
              Security Protocol
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white">Create New Password</h1>
            <p className="text-xs text-white/50">
              Set a strong, NIST-aligned password to secure your authenticity portal
            </p>
          </div>

          {submitted ? (
            <div className="space-y-4 py-4 text-center">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-status-safe/10 border border-status-safe/30 flex items-center justify-center">
                <CheckCircle2 className="w-6 h-6 text-status-safe" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-white">Password Updated</h3>
                <p className="text-xs text-white/70 leading-relaxed">
                  Your credentials have been securely updated using Argon2id. All previous sessions have been invalidated.
                </p>
              </div>
              <Link href="/auth/login" className="block pt-2">
                <GlassButton variant="primary" size="md" className="w-full shadow-glow-blue">
                  Sign In to Privacy Eye
                </GlassButton>
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              {/* Reset Token Input */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-white/70">Reset Authorization Token</label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                  <input
                    type="text"
                    placeholder="Paste recovery token or link"
                    className="glass-input pl-11 text-xs font-mono"
                    {...register('token', { required: 'Reset token is required' })}
                  />
                </div>
                {errors.token && (
                  <p className="text-xs text-status-danger">{errors.token.message}</p>
                )}
              </div>

              {/* New Password */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-white/70">New Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Min 8 characters, uppercase & digit"
                    className="glass-input pl-11 pr-11 text-sm"
                    {...register('new_password', {
                      required: 'New password is required',
                      minLength: { value: 8, message: 'Minimum 8 characters' },
                    })}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.new_password && (
                  <p className="text-xs text-status-danger">{errors.new_password.message}</p>
                )}
              </div>

              {/* Confirm Password */}
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-white/70">Confirm New Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Re-enter new password"
                    className="glass-input pl-11 text-sm"
                    {...register('confirm_password', { required: 'Please confirm password' })}
                  />
                </div>
                {errors.confirm_password && (
                  <p className="text-xs text-status-danger">{errors.confirm_password.message}</p>
                )}
              </div>

              {/* NIST Password Policy Meter */}
              <div className="p-3 rounded-2xl bg-white/[0.03] border border-white/6 space-y-2 text-[11px]">
                <span className="font-semibold text-white/60 tracking-wider uppercase text-[10px]">
                  Complexity Requirements
                </span>
                <div className="grid grid-cols-3 gap-2">
                  <div className={`flex items-center gap-1.5 ${hasMinLen ? 'text-status-safe' : 'text-white/40'}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${hasMinLen ? 'bg-status-safe' : 'bg-white/20'}`} />
                    <span>8+ Chars</span>
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasUpper ? 'text-status-safe' : 'text-white/40'}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${hasUpper ? 'bg-status-safe' : 'bg-white/20'}`} />
                    <span>1 Uppercase</span>
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasDigit ? 'text-status-safe' : 'text-white/40'}`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${hasDigit ? 'bg-status-safe' : 'bg-white/20'}`} />
                    <span>1 Digit</span>
                  </div>
                </div>
              </div>

              <GlassButton
                type="submit"
                variant="primary"
                size="lg"
                isLoading={loading}
                className="w-full shadow-glow-blue mt-2"
                icon={<ArrowRight className="w-4 h-4" />}
              >
                Update Password
              </GlassButton>
            </form>
          )}

          <div className="pt-4 border-t border-white/6 text-center text-xs text-white/50">
            Return to{' '}
            <Link href="/auth/login" className="text-brand-blue font-semibold hover:underline">
              Sign In
            </Link>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-canvas text-white/50 text-xs font-mono">
        Loading Recovery Engine...
      </div>
    }>
      <ResetPasswordContent />
    </Suspense>
  )
}
