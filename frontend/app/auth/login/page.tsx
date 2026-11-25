'use client'
import React, { useState, Suspense } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Lock, Mail, ArrowRight } from 'lucide-react'
import toast from 'react-hot-toast'

import { useAuth } from '@/contexts/AuthContext'
import { getErrorMessage } from '@/lib/api'
import { BrandLogo } from '@/components/layout/BrandLogo'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import Beams from '@/components/reactbits/Beams'
import DecryptedText from '@/components/reactbits/DecryptedText'
import { AgentWaveCanvas } from '@/components/motion/AgentWaveCanvas'

interface LoginForm {
  email: string
  password: string
  remember_me: boolean
}

function LoginFormContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const rawNext = searchParams.get('next')
  const nextUrl = rawNext && !rawNext.startsWith('/auth') ? rawNext : '/dashboard'
  const { login, isAuthenticated, isLoading } = useAuth()

  // If already authenticated, redirect straight to dashboard
  React.useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace(nextUrl)
    }
  }, [isAuthenticated, isLoading, nextUrl, router])

  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    defaultValues: {
      remember_me: true,
    },
  })

  const onSubmit = async (data: LoginForm) => {
    setLoading(true)
    try {
      await login(data.email, data.password, data.remember_me)
      toast.success('Authentication confirmed.')
      router.replace(nextUrl)
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-canvas relative overflow-hidden">
      {/* Agent Wave Waveform + React Bits Volumetric Beams */}
      <div className="absolute inset-0 pointer-events-none z-0">
        <AgentWaveCanvas className="absolute inset-0" opacity={0.45} speed={0.011} amplitude={34} />
        <Beams
          color="#ffffff"
          opacity={0.14}
          beamWidth={2.2}
          speed={1.1}
          mouseInteraction={true}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20, filter: 'blur(8px)' }}
        animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
        transition={{ duration: 0.75, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-md relative z-10"
      >
        <div className="flex justify-center mb-8">
          <BrandLogo size="lg" />
        </div>

        <GlassCard variant="floating" className="p-8 md:p-10 space-y-6 border border-white/14">
          <div className="text-center space-y-1">
            <span className="text-xs uppercase font-mono tracking-widest text-white/80 block">
              <DecryptedText
                text="Secure Perimeter Access"
                animateOn="view"
                sequential
                speed={40}
              />
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Sign In to{' '}
              <span className="font-editorial-italic text-[#b4b4bc] text-[1.12em]">
                Privacy Eye
              </span>
            </h1>
            <p className="text-xs text-[#9a9a9a]">Enter credentials to unlock active protection</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-white/70">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  type="email"
                  placeholder="analyst@enterprise.com"
                  className="glass-input pl-11"
                  {...register('email', { required: 'Email address is required' })}
                />
              </div>
              {errors.email && (
                <p className="text-xs text-status-danger">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-semibold text-white/70">Password</label>
                <Link
                  href="/auth/forgot-password"
                  className="text-[11px] text-white/70 cursor-pointer hover:underline hover:text-white"
                >
                  Forgot?
                </Link>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••••••"
                  className="glass-input pl-11 pr-11"
                  {...register('password', { required: 'Password is required' })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/40 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-xs text-status-danger">{errors.password.message}</p>
              )}
            </div>

            {/* Remember Me Checkbox */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded bg-white/10 border-white/20 text-white focus:ring-white/30 focus:ring-offset-0 transition-colors"
                  {...register('remember_me')}
                />
                <span className="text-xs text-white/70 hover:text-white transition-colors">
                  Remember me on this device
                </span>
              </label>
            </div>

            <GlassButton
              type="submit"
              variant="primary"
              size="lg"
              isLoading={loading}
              className="w-full mt-2 btn-liquid-metal"
              icon={<ArrowRight className="w-4 h-4" />}
            >
              Sign In
            </GlassButton>
          </form>

          <div className="pt-4 border-t border-white/6 text-center text-xs text-white/50">
            Don't have an account?{' '}
            <Link href="/auth/register" className="text-white font-semibold hover:underline">
              Create Account
            </Link>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-canvas" />}>
      <LoginFormContent />
    </Suspense>
  )
}
