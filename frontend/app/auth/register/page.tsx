'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Lock, Mail, User, ArrowRight, Check } from 'lucide-react'
import toast from 'react-hot-toast'

import { useAuth } from '@/contexts/AuthContext'
import { getErrorMessage } from '@/lib/api'
import { BrandLogo } from '@/components/layout/BrandLogo'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'

interface RegisterForm {
  full_name: string
  email: string
  password: string
  confirm_password: string
  accept_terms: boolean
}

export default function RegisterPage() {
  const router = useRouter()
  const { register: authRegister } = useAuth()
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterForm>()

  const password = watch('password', '')

  const strengthRules = [
    { label: '8+ chars', met: password.length >= 8 },
    { label: 'Uppercase', met: /[A-Z]/.test(password) },
    { label: 'Number', met: /[0-9]/.test(password) },
  ]

  const onSubmit = async (data: RegisterForm) => {
    if (!data.accept_terms) {
      toast.error('You must accept the terms of service to proceed.')
      return
    }
    if (data.password !== data.confirm_password) {
      toast.error('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      await authRegister(data.email, data.password, data.confirm_password, data.full_name)
      toast.success('Account created! Welcome to Privacy Eye.')
      router.push('/dashboard')
    } catch (err) {
      toast.error(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-canvas relative">
      {/* Background ambient lighting */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-white/[0.025] rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-white/[0.02] rounded-full blur-[100px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md my-8"
      >
        <div className="flex justify-center mb-8">
          <BrandLogo size="lg" />
        </div>

        <GlassCard variant="floating" className="p-8 md:p-10 space-y-6 border border-white/14">
          <div className="text-center space-y-1">
            <span className="text-xs uppercase font-mono tracking-widest text-white/80">
              Autonomous Verification
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-white">Create Account</h1>
            <p className="text-xs text-white/50">Gain full access to real-time biometric defense</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-white/70">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  type="text"
                  placeholder="Harshvardhan"
                  className="glass-input pl-11"
                  {...register('full_name', { required: 'Full name is required' })}
                />
              </div>
              {errors.full_name && (
                <p className="text-xs text-status-danger">{errors.full_name.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-white/70">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  type="email"
                  placeholder="analyst@agency.gov"
                  className="glass-input pl-11"
                  {...register('email', { required: 'Email address is required' })}
                />
              </div>
              {errors.email && (
                <p className="text-xs text-status-danger">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-white/70">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••••••"
                  className="glass-input pl-11 pr-11"
                  {...register('password', {
                    required: 'Password is required',
                    minLength: { value: 8, message: 'Minimum 8 characters' },
                  })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/40 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Password strength tags */}
              <div className="flex gap-2 pt-1">
                {strengthRules.map((rule, idx) => (
                  <span
                    key={idx}
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-md flex items-center gap-1 ${
                      rule.met ? 'bg-status-safe/15 text-status-safe' : 'bg-white/5 text-white/30'
                    }`}
                  >
                    <Check className={`w-3 h-3 ${rule.met ? 'opacity-100' : 'opacity-0'}`} />
                    {rule.label}
                  </span>
                ))}
              </div>
              {errors.password && (
                <p className="text-xs text-status-danger">{errors.password.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-white/70">Confirm Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="••••••••••••"
                  className="glass-input pl-11 pr-11"
                  {...register('confirm_password', {
                    required: 'Confirming password is required',
                    validate: (val) => val === password || 'Passwords do not match',
                  })}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/40 hover:text-white transition-colors"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.confirm_password && (
                <p className="text-xs text-status-danger">{errors.confirm_password.message}</p>
              )}
            </div>

            {/* Accept Terms Checkbox */}
            <div className="pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  className="w-4 h-4 rounded bg-white/10 border-white/20 text-white focus:ring-white/30 focus:ring-offset-0 transition-colors"
                  {...register('accept_terms', { required: 'You must accept the terms' })}
                />
                <span className="text-xs text-white/70">
                  I accept the Privacy Eye terms &amp;{' '}
                  <Link href="/privacy" className="text-white underline underline-offset-2 hover:text-white/80 transition-colors" target="_blank">
                    Privacy Policy
                  </Link>
                </span>
              </label>
              {errors.accept_terms && (
                <p className="text-xs text-status-danger mt-1">{errors.accept_terms.message}</p>
              )}
            </div>

            <GlassButton
              type="submit"
              variant="primary"
              size="lg"
              isLoading={loading}
              className="w-full mt-2"
              icon={<ArrowRight className="w-4 h-4" />}
            >
              Create Account
            </GlassButton>
          </form>

          <div className="pt-4 border-t border-white/6 text-center text-xs text-white/50">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-white font-semibold hover:underline">
              Sign In
            </Link>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
